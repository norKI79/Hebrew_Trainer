# -*- coding: utf-8 -*-
import sqlite3
import os

DBNAME = "hebrew.db"
WORDS_FILE = "hebrew_words.txt"       # format: hebrew<TAB>english
EXAMPLES_FILE = "hebrew_examples.txt" # format: hebrew_word<TAB>hebrew_phrase<TAB>english_phrase

# ---------- Delete old DB ----------
if os.path.exists(DBNAME):
    print(f"Deleting old database: {DBNAME}")
    os.remove(DBNAME)

conn = sqlite3.connect(DBNAME)
c = conn.cursor()

# ---------- Create tables ----------
c.execute("""
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hebrew TEXT NOT NULL,
    english TEXT NOT NULL,
    mp3_file TEXT
)
""")

c.execute("""
CREATE TABLE examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    hebrew_phrase TEXT NOT NULL,
    english_phrase TEXT NOT NULL,
    mp3_file TEXT,
    FOREIGN KEY(word_id) REFERENCES words(id)
)
""")

conn.commit()
print("Tables created successfully!")

# ---------- Load words from file ----------
if not os.path.exists(WORDS_FILE):
    raise FileNotFoundError(f"{WORDS_FILE} not found!")

with open(WORDS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or "\t" not in line:
            continue
        heb, eng = line.split("\t", 1)
        c.execute("INSERT INTO words (hebrew, english) VALUES (?, ?)", (heb, eng))

conn.commit()
print("Words loaded successfully!")

# ---------- Load examples from file ----------
if os.path.exists(EXAMPLES_FILE):
    with open(EXAMPLES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "\t" not in line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            word_heb, heb_phrase, eng_phrase = parts

            # Lookup word_id from DB
            c.execute("SELECT id FROM words WHERE hebrew=?", (word_heb,))
            row = c.fetchone()
            if not row:
                print(f"Word not found in DB, skipping example: {word_heb}")
                continue
            word_id = row[0]

            c.execute(
                "INSERT INTO examples (word_id, hebrew_phrase, english_phrase) VALUES (?, ?, ?)",
                (word_id, heb_phrase, eng_phrase)
            )

    conn.commit()
    print("Examples loaded successfully!")
else:
    print(f"No examples file found ({EXAMPLES_FILE}), skipping.")

conn.close()
print("Database setup complete!")
