"""
database_manager.py

Local SQLite storage for Cooking Ina recipes.

The tables mirror the dictionary produced by recipe_parser.py:

    recipes      ->  recipe["title"]
    ingredients  ->  recipe["ingredients"]                (one row per item)
    sections     ->  recipe["sections"]                   (name, time, duration_seconds)
    steps        ->  recipe["sections"][n]["steps"]       (one row per instruction)

recipe["steps"] (the flattened list the UI uses) is not stored. It is rebuilt
from the sections whenever a recipe is read back.

Public functions:
    initialize_database()    create cooking_ina.db and its tables if missing
    save_recipe(recipe)      store one recipe dictionary, returns its id
    get_all_recipes()        every saved recipe, newest first, as parser-style dicts
    delete_recipe(id)        remove a recipe and everything that belongs to it
"""

import hashlib
import json
import os
import sqlite3
import sys
from contextlib import contextmanager

DB_FILENAME = "cooking_ina.db"

# Same fallback duration recipe_parser.py uses when a section has no time
DEFAULT_DURATION_SECONDS = 1800


def _default_db_path():
    # Keep the database next to the app instead of the current working
    # directory, so it is the same file no matter how the app is launched.
    # (A PyInstaller build must not use sys._MEIPASS here: that folder is
    # deleted every time the app closes.)
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_dir, DB_FILENAME)


DB_PATH = _default_db_path()


SCHEMA = """
CREATE TABLE IF NOT EXISTS recipes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    content_hash  TEXT    NOT NULL UNIQUE,
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingredients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id   INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    item_text   TEXT    NOT NULL,
    UNIQUE (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS sections (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id         INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position          INTEGER NOT NULL,
    name              TEXT    NOT NULL,
    time              TEXT    NOT NULL DEFAULT '',
    duration_seconds  INTEGER NOT NULL DEFAULT 1800,
    UNIQUE (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS steps (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id        INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    position          INTEGER NOT NULL,
    instruction_text  TEXT    NOT NULL,
    UNIQUE (section_id, position)
);
"""


@contextmanager
def _connect(db_path=None):
    """Open a connection that commits on success, rolls back on error, and always closes."""
    connection = sqlite3.connect(db_path or DB_PATH)

    # SQLite ignores foreign keys (and ON DELETE CASCADE) unless this is on
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path=None):
    """Create the database file and its tables if they do not exist yet."""
    with _connect(db_path) as connection:
        connection.executescript(SCHEMA)


# Cleaning helpers: make any recipe dictionary safe to store

def _clean_text(value):
    return "" if value is None else str(value).strip()


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _to_seconds(value):
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return DEFAULT_DURATION_SECONDS


def _normalize_recipe(recipe):
    """Return a cleaned copy of the recipe containing only what the database stores."""
    if not isinstance(recipe, dict):
        raise ValueError("A recipe must be a dictionary.")

    ingredients = [
        text
        for text in (_clean_text(item) for item in _as_list(recipe.get("ingredients")))
        if text
    ]

    sections = []

    for raw_section in _as_list(recipe.get("sections")):
        if not isinstance(raw_section, dict):
            continue

        steps = [
            text
            for text in (_clean_text(step) for step in _as_list(raw_section.get("steps")))
            if text
        ]

        sections.append({
            "name": _clean_text(raw_section.get("name")) or "Recipe Step",
            "time": _clean_text(raw_section.get("time")),
            "duration_seconds": _to_seconds(raw_section.get("duration_seconds")),
            "steps": steps
        })

    if not sections:
        raise ValueError("A recipe needs at least one section to be saved.")

    return {
        "title": _clean_text(recipe.get("title")) or "Untitled Recipe",
        "ingredients": ingredients,
        "sections": sections
    }


def _fingerprint(data):
    """Hash of a cleaned recipe, used to spot a recipe that is already saved."""
    canonical = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def save_recipe(recipe, db_path=None):
    """
    Save a recipe dictionary (the format recipe_parser.py returns).

    Returns the recipe's database id. If an identical recipe is already
    saved, nothing is added and the existing id is returned, so uploading
    the same file twice does not create duplicates.
    """
    data = _normalize_recipe(recipe)
    fingerprint = _fingerprint(data)

    with _connect(db_path) as connection:
        existing = connection.execute(
            "SELECT id FROM recipes WHERE content_hash = ?",
            (fingerprint,)
        ).fetchone()

        if existing:
            return existing[0]

        recipe_id = connection.execute(
            "INSERT INTO recipes (title, content_hash) VALUES (?, ?)",
            (data["title"], fingerprint)
        ).lastrowid

        connection.executemany(
            "INSERT INTO ingredients (recipe_id, position, item_text) VALUES (?, ?, ?)",
            [
                (recipe_id, position, text)
                for position, text in enumerate(data["ingredients"])
            ]
        )

        for position, section in enumerate(data["sections"]):
            section_id = connection.execute(
                "INSERT INTO sections (recipe_id, position, name, time, duration_seconds) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    recipe_id,
                    position,
                    section["name"],
                    section["time"],
                    section["duration_seconds"]
                )
            ).lastrowid

            connection.executemany(
                "INSERT INTO steps (section_id, position, instruction_text) VALUES (?, ?, ?)",
                [
                    (section_id, step_position, text)
                    for step_position, text in enumerate(section["steps"])
                ]
            )

    return recipe_id


def get_all_recipes(db_path=None):
    """
    Return every saved recipe, newest first, as a list of dictionaries:

    {
        "id": int,
        "title": str,
        "ingredients": [str, ...],
        "sections": [
            {
                "name": str,
                "time": str,
                "duration_seconds": int,
                "steps": [str, ...]
            }
        ],
        "steps": [str, ...]
    }

    Apart from the extra "id" key this is the same shape recipe_parser.py
    returns, so a result can be handed straight to the UI.
    """
    with _connect(db_path) as connection:
        recipe_rows = connection.execute(
            "SELECT id, title FROM recipes ORDER BY id DESC"
        ).fetchall()

        # Read each table once and group in Python (4 queries in total,
        # no matter how many recipes are saved)
        ingredients_by_recipe = {}

        for recipe_id, item_text in connection.execute(
            "SELECT recipe_id, item_text FROM ingredients ORDER BY recipe_id, position"
        ):
            ingredients_by_recipe.setdefault(recipe_id, []).append(item_text)

        steps_by_section = {}

        for section_id, instruction_text in connection.execute(
            "SELECT section_id, instruction_text FROM steps ORDER BY section_id, position"
        ):
            steps_by_section.setdefault(section_id, []).append(instruction_text)

        sections_by_recipe = {}

        for section_id, recipe_id, name, time_text, duration_seconds in connection.execute(
            "SELECT id, recipe_id, name, time, duration_seconds "
            "FROM sections ORDER BY recipe_id, position"
        ):
            sections_by_recipe.setdefault(recipe_id, []).append({
                "name": name,
                "time": time_text,
                "duration_seconds": duration_seconds,
                "steps": steps_by_section.get(section_id, [])
            })

    recipes = []

    for recipe_id, title in recipe_rows:
        sections = sections_by_recipe.get(recipe_id, [])

        recipes.append({
            "id": recipe_id,
            "title": title,
            "ingredients": ingredients_by_recipe.get(recipe_id, []),
            "sections": sections,
            # UI Compatibility (same flattened list recipe_parser.py builds)
            "steps": [
                step
                for section in sections
                for step in section["steps"]
            ]
        })

    return recipes


def delete_recipe(recipe_id, db_path=None):
    """Delete a saved recipe. Returns True if a recipe was removed."""
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM recipes WHERE id = ?",
            (recipe_id,)
        )

        return cursor.rowcount > 0


if __name__ == "__main__":
    # Quick check from the terminal:  python database_manager.py
    initialize_database()
    saved = get_all_recipes()

    print(f"Database: {DB_PATH}")
    print(f"{len(saved)} saved recipe(s)")

    for item in saved:
        print(f"  [{item['id']}] {item['title']} - {len(item['sections'])} sections")
