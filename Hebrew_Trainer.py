# -*- coding: utf-8 -*-
import os
import tkinter as tk
from gtts import gTTS
import pygame
import threading
import sqlite3

# ---------- Directories ----------
MP3_DIR = "tts_files"
os.makedirs(MP3_DIR, exist_ok=True)
DBNAME = "hebrew.db"

# ---------- Initialize pygame mixer ----------
try:
    pygame.mixer.init()
except Exception as e:
    print(f"Pygame mixer init failed: {e}")

# ---------- Database loading ----------
def load_words():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute("SELECT id, hebrew, english, mp3_file FROM words ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def load_examples(word_id):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute("SELECT id, hebrew_phrase, english_phrase, mp3_file FROM examples WHERE word_id=? ORDER BY id", (word_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# ---------- TTS playback ----------
def speak_hebrew_db(item_id, is_example=False):
    """Play Hebrew word or example, generate MP3 if needed."""
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    if not is_example:
        c.execute("SELECT hebrew, mp3_file FROM words WHERE id=?", (item_id,))
    else:
        c.execute("SELECT hebrew_phrase, mp3_file FROM examples WHERE id=?", (item_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return

    heb_text, mp3_file = row

    # Generate MP3 if missing
    if not mp3_file or not os.path.exists(mp3_file):
        safe_name = heb_text.replace(" ", "_").replace("/", "_")
        mp3_file = os.path.join(MP3_DIR, f"{safe_name}.mp3")
        tts = gTTS(text=heb_text, lang="iw")
        tts.save(mp3_file)
        # Update DB
        conn = sqlite3.connect(DBNAME)
        c = conn.cursor()
        if not is_example:
            c.execute("UPDATE words SET mp3_file=? WHERE id=?", (mp3_file, item_id))
        else:
            c.execute("UPDATE examples SET mp3_file=? WHERE id=?", (mp3_file, item_id))
        conn.commit()
        conn.close()

    # Play MP3 asynchronously
    def _play():
        try:
            pygame.mixer.music.load(mp3_file)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing TTS: {e}")

    threading.Thread(target=_play, daemon=True).start()

# ---------- GUI ----------
root = tk.Tk()
root.title("Hebrew Trainer 1.0")
root.geometry("700x550")

# ---------- Title ----------
title_label = tk.Label(root, text="Hebrew Trainer 1.0", font=("Arial", 24, "bold"), pady=10)
title_label.pack(side="top", fill="x")

# ---------- Scrollable Canvas ----------
container = tk.Frame(root)
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container)
scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Scrollable frame inside canvas
scroll_frame = tk.Frame(canvas)
window_id = canvas.create_window((0,0), window=scroll_frame, anchor="nw")

# Update scrollregion when frame changes size
def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scroll_frame.bind("<Configure>", on_frame_configure)

# Allow scrolling with mouse wheel
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# ---------- Highlight management ----------
current_highlight = None

def highlight_label(label):
    global current_highlight
    if current_highlight and current_highlight.winfo_exists():
        current_highlight.config(bg="white")
    label.config(bg="lightblue")
    current_highlight = label
    label.update_idletasks()

def clear_scroll_frame():
    for widget in scroll_frame.winfo_children():
        widget.destroy()

# ---------- Top button ----------
top_button = tk.Button(root, text="Back to Words", font=("Arial", 14), command=lambda: display_words())

# ---------- Display words ----------
def display_words():
    clear_scroll_frame()
    top_button.pack_forget()
    words = load_words()
    scroll_frame.columnconfigure(0, weight=1)
    scroll_frame.columnconfigure(1, weight=1)

    for i, (word_id, heb, eng, mp3_file) in enumerate(words):
        # Hebrew label (left)
        lbl_he = tk.Label(scroll_frame, text=heb, font=("Arial", 18),
                          anchor="w", justify="left", bg="white", padx=5)
        lbl_he.grid(row=i, column=0, sticky="w", padx=(5,10), pady=2)
        lbl_he.bind("<Button-1>", lambda e, lbl=lbl_he, wid=word_id: [highlight_label(lbl), speak_hebrew_db(wid)])
        lbl_he.bind("<Button-3>", lambda e, wid=word_id: display_examples(wid))

        # English label (right)
        lbl_en = tk.Label(scroll_frame, text=eng, font=("Arial", 14),
                          anchor="e", justify="right", bg="white", padx=5)
        lbl_en.grid(row=i, column=1, sticky="e", padx=(10,5), pady=2)

# ---------- Display examples ----------
def display_examples(word_id):
    clear_scroll_frame()
    top_button.pack(side="top", fill="x")
    examples = load_examples(word_id)
    scroll_frame.columnconfigure(0, weight=1)
    scroll_frame.columnconfigure(1, weight=1)

    canvas.yview_moveto(0)  # Scroll back to top

    for i, (ex_id, heb, eng, mp3_file) in enumerate(examples):
        # Hebrew example (left)
        lbl_he = tk.Label(scroll_frame, text=heb, font=("Arial", 18),
                          anchor="w", justify="left", bg="white", padx=5)
        lbl_he.grid(row=i, column=0, sticky="w", padx=(5,10), pady=2)
        lbl_he.bind("<Button-1>", lambda e, lbl=lbl_he, exid=ex_id: [highlight_label(lbl), speak_hebrew_db(exid, is_example=True)])

        # English example (right)
        lbl_en = tk.Label(scroll_frame, text=eng, font=("Arial", 14),
                          anchor="e", justify="right", bg="white", padx=5)
        lbl_en.grid(row=i, column=1, sticky="e", padx=(10,5), pady=2)

# ---------- Instruction label ----------
instruction_label = tk.Label(root, text="Left click to highlight & play, Right click to see examples.",
                             font=("Arial", 12), pady=10)
instruction_label.pack(side="bottom", fill="x")

# ---------- Start ----------
display_words()
root.mainloop()
