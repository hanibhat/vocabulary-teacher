# Vocabulary Teacher

A small browser app for loading vocabulary from a local `.txt` file and practicing random word sets.

## What It Does

- Loads a user-selected `.txt` vocabulary file.
- Parses source phrases, translations, and optional examples.
- Groups entries by category.
- Stores successfully parsed vocabulary in `localStorage` so it is restored when the app is opened again.
- Lets you choose a random number of entries to study.
- Supports filtering across source text, translation, examples, and categories.

## File Format

By default:

- Category lines start with `#`.
- Columns are separated by four spaces.
- Column 1 is the source phrase.
- Column 2 is the translation.
- Column 3 is optional example text.

Example:

```text
# Random
Schrecklich    terrible, awful    Das ist schrecklich.
Vorzüglich    excellent

# Verben
geben    to give    Ich gebe dir das Buch.
```

The category prefix and column separator can be changed from the app settings menu.

## Running

Open `index.html` in a browser, or host the folder with any static web server.
