"""
recipe_parser.py

Recipe file parsing backend for Cooking Ina.

The parser treats each [SECTION] as one cooking stage.
Each stage contains:
    - name
    - time
    - parsed timer duration
    - instructions

Supported file types:
    - TXT
    - JSON
    - PDF (requires PyPDF2)
"""

import json
import os
import re

# Handles recipe files and their timing information

def parse_time_to_seconds(time_text):
    # Converts the recipe time into seconds for the timer
    """
    Convert recipe timing such as:
        3 mins + 3 mins buffer
        30 mins + 3 mins buffer
        2-3 mins + 3 mins buffer
        1-2 mins + 3 mins buffer

    into a concrete timer duration in seconds.

    For a time range, the upper value is used for the countdown.
    """
    if not time_text:
        return 1800

    text = time_text.lower().strip()

    # Get the main cooking time
    main_match = re.search(r"(\d+)\s*-\s*(\d+)\s*min", text)
    single_match = re.search(r"(\d+)\s*min", text)

    if main_match:
        base_minutes = int(main_match.group(2))
    elif single_match:
        base_minutes = int(single_match.group(1))
    else:
        return 1800

    # Add the extra buffer time
    buffer_match = re.search(r"(\d+)\s*min(?:s)?\s*buffer", text)
    buffer_minutes = int(buffer_match.group(1)) if buffer_match else 0

    return (base_minutes + buffer_minutes) * 60


def parse_recipe_file(file_path):
    # Select the parser based on the file type
    """Parse a recipe file and return a normalized recipe dictionary."""

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".txt":
        return parse_txt(file_path)
    if extension == ".json":
        return parse_json(file_path)
    if extension == ".pdf":
        return parse_pdf(file_path)

    raise ValueError(f"Unsupported file type: {extension}")


def parse_txt(file_path):
    # Read the recipe text file
    """Parse the project's structured TXT recipe format."""

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    return parse_recipe_text(text)


def parse_recipe_text(text):
    # Read the recipe one line at a time
    """
    Parse recipe text into:

    {
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
    """

    lines = [line.strip() for line in text.splitlines()]

    title = "Untitled Recipe"
    ingredients = []
    sections = []

    current_section = None
    in_ingredients = False

    # Check each line for recipe information
    for raw_line in lines:
        if not raw_line:
            continue

        recipe_match = re.match(
            r"^RECIPE\s*:\s*(.+)$",
            raw_line,
            re.IGNORECASE
        )

        if recipe_match:
            title = recipe_match.group(1).strip()
            in_ingredients = False
            continue

        if re.match(
            r"^INGREDIENTS\s*:\s*$",
            raw_line,
            re.IGNORECASE
        ):
            in_ingredients = True
            current_section = None
            continue

        section_match = re.match(r"^\[(.+)\]$", raw_line)

        if section_match:
            section_name = section_match.group(1).strip()

            current_section = {
                "name": section_name,
                "time": "",
                # Store the timer duration
                "duration_seconds": 1800,
                "steps": []
            }

            sections.append(current_section)
            in_ingredients = False
            continue

        time_match = re.match(
            r"^TIME\s*:\s*(.+)$",
            raw_line,
            re.IGNORECASE
        )

        if time_match and current_section is not None:
            current_section["time"] = time_match.group(1).strip()

            # convert time for the timer
            current_section["duration_seconds"] = parse_time_to_seconds(
                current_section["time"]
            )
            continue

        if in_ingredients:
            ingredient = re.sub(
                r"^[-*]\s*",
                "",
                raw_line
            ).strip()

            if ingredient:
                ingredients.append(ingredient)

            continue

        if raw_line.upper() in {
            "PROCESS:",
            "PROCESS",
            "PREPARATION:",
            "PREPARATION"
        }:
            continue

        if current_section is not None:
            step = re.sub(
                r"^\d+[\.\)]\s*",
                "",
                raw_line
            )

            step = re.sub(
                r"^[-*]\s*",
                "",
                step
            ).strip()

            if step:
                current_section["steps"].append(step)

    # UI Compatiblity
    flattened_steps = [
        step
        for section in sections
        for step in section["steps"]
    ]

    return {
        "title": title,
        "ingredients": ingredients,
        "sections": sections,
        "steps": flattened_steps
    }


def parse_json(file_path):
    # Read a structured JSON recipe
    """Parse a structured JSON recipe."""

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Recipe JSON must contain an object.")

    title = str(data.get("title", "Untitled Recipe"))
    ingredients = [
        str(item)
        for item in data.get("ingredients", [])
    ]

    sections = []

    raw_sections = data.get("sections", [])

    if isinstance(raw_sections, list):
        for item in raw_sections:
            if not isinstance(item, dict):
                continue

            name = str(item.get("name", "Recipe Step"))
            time = str(item.get("time", ""))
            raw_steps = item.get("steps", [])

            if isinstance(raw_steps, list):
                steps = [str(step) for step in raw_steps]
            else:
                steps = [str(raw_steps)]

            sections.append({
                "name": name,
                "time": time,
                # Added by Ran-Ran
                "duration_seconds": parse_time_to_seconds(time),
                "steps": steps
            })

    if not sections and isinstance(data.get("steps"), list):
        sections.append({
            "name": "Recipe Steps",
            "time": "",
            # Default timer duration
            "duration_seconds": 1800,
            "steps": [str(step) for step in data["steps"]]
        })

    flattened_steps = [
        step
        for section in sections
        for step in section["steps"]
    ]

    return {
        "title": title,
        "ingredients": ingredients,
        "sections": sections,
        "steps": flattened_steps
    }


def parse_pdf(file_path):
    # Extract text from the PDF first
    """Extract PDF text and parse it using the recipe text parser."""

    try:
        from PyPDF2 import PdfReader
    except ImportError as error:
        raise ImportError(
            "PDF support requires PyPDF2. "
            "Install it with: pip install PyPDF2"
        ) from error

    reader = PdfReader(file_path)
    pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            pages.append(page_text)

    text = "\n".join(pages)

    if not text.strip():
        raise ValueError("The PDF did not contain extractable text.")

    return parse_recipe_text(text)


def recipe_to_timer_data(recipe):
    # Give the UI the recipe sections it needs
    """
    Return the recipe sections in the form needed by the timer UI.

    Each section is one timer stage, rather than each instruction
    becoming a separate timed step.
    """
    return recipe["title"], recipe["sections"]
