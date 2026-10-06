# Cooking Ina - Digital Cooking Assistant GUI

A desktop graphical user interface for **Cooking Ina**, built using Python and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter). Designed with a warm **Burnt Rust** color palette, a Pomodoro-style step timer, and backend event hooks ready for module integration.

## Requirements

- Python 3.14
- CustomTkinter
- tkinterdnd2
- pygame-ce
- PyPDF2
- anyio

## Installation

Install the required packages with:

```bash
py -m pip install customtkinter tkinterdnd2 pygame-ce PyPDF2 anyio
```

Then run:

```bash
py cooking_ina_ui.py
```

## Making a Recipe

Recipe files use this format:

```text
RECIPE: Example Recipe

INGREDIENTS:
- Ingredient 1
- Ingredient 2

[Prep - Example]
TIME: 5 mins + 3 mins buffer

- Prepare the ingredients.
- Get everything ready.

[Process - Example]
TIME: 20 mins + 3 mins buffer

- Start cooking.
- Continue until done.

[Finalization - Example]
TIME: 5 mins + 3 mins buffer

- Finish the dish.
- Serve.
```

### Format

- `RECIPE:` is the recipe name.
- `INGREDIENTS:` lists the ingredients.
- `[Section Name]` starts a cooking section.
- `TIME:` sets the timer for that section.
- Lines starting with `-` are the instructions.

Each section gets its own timer.

For example:

```text
[Process - Pasta]
TIME: 15 mins + 3 mins buffer

- Boil the water.
- Add the pasta.
```

This gives the section a 18 minute timer.

For a time range like:

```text
TIME: 2-3 mins + 3 mins buffer
```

the timer uses the higher number, so it becomes 6 minutes.

## Uploading Recipes

Recipes can be uploaded as:

- `.txt`
- `.json`
- `.pdf`

You can either select the file or drag and drop it into the app.

PDF files need PyPDF2.

## Manual Entry

You can also make a recipe inside the app.

1. Click **Manual Entry**.
2. Enter the recipe name.
3. Click **+ Add Step**.
4. Enter the instruction and time.
5. Click **Save Step**.
6. Add more steps if needed.
7. Click **Start Cooking**.

## Saved Recipes

Recipes can be saved locally and accessed through **View Saved Recipes**.

The app uses a local `cooking_ina.db` database for this.

## Cooking Features

The cooking screen has:

- Recipe checklist
- Timer
- Repeat Step
- Next Step
- `+1 Min`
- Time stamps
- Actual vs Expected time
- Add Step while cooking

The app also keeps cooking metrics when a recipe is completed.
