"""URL_Shortening.py"""

import sqlite3
import tkinter as tk
from tkinter import messagebox
import urllib.parse
import urllib.request

from Database import DB_FILE
from URL_Shtng_style import COLORS, FONT


def save_url(original_url, short_url):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shortened_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO shortened_urls (original_url, short_url) VALUES (?, ?)",
            (original_url, short_url)
        )


def shorten_url(original_url):
    """Create a working short link through TinyURL."""
    api_url = "https://tinyurl.com/api-create.php?" + urllib.parse.urlencode(
        {"url": original_url}
    )
    request = urllib.request.Request(
        api_url,
        headers={"User-Agent": "UtilitiesApplication/1.0"},
    )

    with urllib.request.urlopen(request, timeout=4) as response:
        short_url = response.read().decode("utf-8").strip()

    parsed_url = urllib.parse.urlparse(short_url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        raise ValueError("The shortening service returned an invalid response.")

    return short_url


def create_gui(parent):
    frame = tk.Frame(parent, bg=COLORS["background"])

    card = tk.Frame(frame, bg=COLORS["card"], padx=35, pady=35)
    card.pack(fill="both", expand=True, padx=35, pady=35)

    tk.Label(
        card, text="URL Shortening", font=(FONT, 22, "bold"),
        bg=COLORS["card"], fg=COLORS["text"]
    ).pack(anchor="w", pady=(0, 8))

    tk.Label(
        card, text="Make your long links shorter and easier to share.",
        font=(FONT, 10), bg=COLORS["card"], fg=COLORS["secondary"]
    ).pack(anchor="w", pady=(0, 25))

    tk.Label(
        card, text="Enter your long URL", font=(FONT, 10, "bold"),
        bg=COLORS["card"], fg=COLORS["text"]
    ).pack(anchor="w")

    url_entry = tk.Entry(
        card, font=(FONT, 11), bg=COLORS["input"], fg=COLORS["text"],
        relief="flat", highlightthickness=1,
        highlightbackground=COLORS["border"], highlightcolor=COLORS["primary"]
    )
    url_entry.pack(fill="x", ipady=12, pady=10)

    tk.Label(
        card, text="Shortened URL", font=(FONT, 10, "bold"),
        bg=COLORS["card"], fg=COLORS["text"]
    ).pack(anchor="w", pady=(15, 0))

    result_entry = tk.Entry(
        card, font=(FONT, 11), bg=COLORS["input"], fg=COLORS["primary_dark"],
        relief="flat", highlightthickness=1, highlightbackground=COLORS["border"],
        state="readonly"
    )
    result_entry.pack(fill="x", ipady=12, pady=10)

    status_label = tk.Label(
        card, text="Your shortened link will appear here.",
        font=(FONT, 9), bg=COLORS["card"], fg=COLORS["secondary"]
    )
    status_label.pack(anchor="w", pady=(0, 10))

    def display_result(short_url):
        result_entry.config(state="normal")
        result_entry.delete(0, tk.END)
        result_entry.insert(0, short_url)
        result_entry.config(state="readonly")

    def generate_short_url():
        original_url = url_entry.get().strip()

        if not original_url:
            messagebox.showwarning("Missing URL", "Please enter a URL first.")
            return

        if not original_url.startswith(("http://", "https://")):
            original_url = "https://" + original_url

        parsed_url = urllib.parse.urlparse(original_url)
        if parsed_url.scheme not in ("http", "https") or not parsed_url.hostname or "." not in parsed_url.hostname:
            messagebox.showerror("Invalid URL", "Please enter a valid website URL.")
            return

        shorten_button.config(state="disabled", text="Shortening...")
        status_label.config(text="Generating your shortened link...")
        frame.update_idletasks()

        try:
            try:
                short_url = shorten_url(original_url)
            except (OSError, UnicodeError, ValueError) as error:
                status_label.config(text="Unable to shorten the URL.")
                messagebox.showerror(
                    "Shortening Failed",
                    f"The shortening service could not create a link:\n{error}",
                )
                return

            save_url(original_url, short_url)
            display_result(short_url)
            status_label.config(text="URL shortened and saved to database!")

        except sqlite3.Error as error:
            status_label.config(text="Unable to save the URL.")
            messagebox.showerror("Database Error", str(error))

        finally:
            shorten_button.config(state="normal", text="Shorten URL")

    def copy_url():
        short_url = result_entry.get()
        if not short_url:
            messagebox.showinfo("No URL", "Please shorten a URL first.")
            return

        frame.clipboard_clear()
        frame.clipboard_append(short_url)
        frame.update()
        status_label.config(text="Shortened URL copied to clipboard!")

    button_frame = tk.Frame(card, bg=COLORS["card"])
    button_frame.pack(anchor="w", pady=15)

    shorten_button = tk.Button(
        button_frame, text="Shorten URL", command=generate_short_url,
        font=(FONT, 10, "bold"), bg=COLORS["primary"], fg="white",
        activebackground=COLORS["primary_dark"], activeforeground="white",
        relief="flat", cursor="hand2", padx=25, pady=11
    )
    shorten_button.pack(side="left", padx=(0, 10))

    tk.Button(
        button_frame, text="Copy URL", command=copy_url,
        font=(FONT, 10, "bold"), bg=COLORS["input"], fg=COLORS["primary_dark"],
        activebackground=COLORS["border"], relief="flat", cursor="hand2",
        padx=25, pady=11
    ).pack(side="left")

    frame.pack(fill="both", expand=True)
    return frame