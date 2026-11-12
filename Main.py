"""
Main.py - Includes Popover Profile Drawer pinned directly under the Profile Button.
"""

import sqlite3
import tkinter as tk
from tkinter import ttk

import auth
import Login
import URL_Shortening
import SMS_and_Email
import FakeDataGeneration
from Database import DB_FILE
from theme_manager import COLORS, FONT, toggle_theme


def get_user_info(username):
    """Fetches user email from SQLite."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            row = conn.execute("SELECT email FROM users WHERE username = ?", (username,)).fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        pass
    return f"{username.lower()}@utilityapp.local"


def show_login(root):
    Login.create_login(
        root,
        lambda username: build_main_app(root, username)
    )


def build_main_app(root, username):
    user_email = get_user_info(username)

    def redraw_ui():
        for widget in root.winfo_children():
            widget.destroy()

        root.title("Utilities Suite")
        Login.center_window(root, 1050, 780)
        root.minsize(900, 680)
        root.configure(bg=COLORS["background"])

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=COLORS["border"],
            foreground=COLORS["secondary"],
            padding=[22, 12],
            font=(FONT, 10, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["primary"])],
            foreground=[("selected", "#FFFFFF")]
        )

        # Header Bar
        header = tk.Frame(root, bg=COLORS["background"])
        header.pack(fill="x", padx=35, pady=(20, 10))

        user_bar = tk.Frame(header, bg=COLORS["background"])
        user_bar.pack(fill="x")

        # Dark / Light Mode Toggle Button
        def handle_theme_toggle():
            toggle_theme()
            redraw_ui()

        btn_theme = tk.Button(
            user_bar,
            text="🌙 Dark Mode" if COLORS["background"] == "#F8FAFC" else "☀️ Light Mode",
            font=(FONT, 9, "bold"),
            bg=COLORS["primary"],
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=handle_theme_toggle
        )
        btn_theme.pack(side="right", padx=(10, 0))

        # --- FLOATING PROFILE DRAWER (Pinned right under the Profile Button) ---
        profile_card = tk.Frame(
            root, bg=COLORS["card"], padx=16, pady=14,
            highlightbackground=COLORS["border"], highlightthickness=1
        )

        tk.Label(
            profile_card, text=f"👤 {username}", font=(FONT, 11, "bold"),
            bg=COLORS["card"], fg=COLORS["text"]
        ).pack(anchor="w")

        tk.Label(
            profile_card, text=user_email, font=(FONT, 8),
            bg=COLORS["card"], fg=COLORS["secondary"]
        ).pack(anchor="w", pady=(1, 6))

        tk.Label(
            profile_card, text="Role: Administrator\nStatus: Active Session",
            font=(FONT, 8), bg=COLORS["card"], fg=COLORS["text"], justify="left"
        ).pack(anchor="w", pady=(0, 10))

        tk.Button(
            profile_card,
            text="Log Out",
            font=(FONT, 8, "bold"),
            bg=COLORS["danger"],
            fg="#FFFFFF",
            activebackground="#DC2626",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=lambda: show_login(root)
        ).pack(fill="x")

        # Animation state and positioning logic
        anim_state = {"visible": False, "target_height": 130, "current_height": 0, "running": False}

        def animate_popover():
            if not anim_state["running"]:
                return

            step = 10
            if anim_state["visible"]:
                if anim_state["current_height"] < anim_state["target_height"]:
                    anim_state["current_height"] = min(
                        anim_state["current_height"] + step, anim_state["target_height"]
                    )
                    profile_card.config(height=anim_state["current_height"])
                    root.after(10, animate_popover)
                else:
                    anim_state["running"] = False
            else:
                if anim_state["current_height"] > 0:
                    anim_state["current_height"] = max(anim_state["current_height"] - step, 0)
                    profile_card.config(height=anim_state["current_height"])
                    root.after(10, animate_popover)
                else:
                    profile_card.place_forget()
                    anim_state["running"] = False

        def toggle_profile_popover():
            if anim_state["running"]:
                return

            anim_state["visible"] = not anim_state["visible"]
            anim_state["running"] = True

            if anim_state["visible"]:
                # Calculate precise absolute screen coordinates under the button
                root.update_idletasks()
                bx = btn_profile.winfo_rootx() - root.winfo_rootx() - 110
                by = btn_profile.winfo_rooty() - root.winfo_rooty() + btn_profile.winfo_height() + 4

                profile_card.place(x=bx, y=by, width=220)
                profile_card.lift()
                btn_profile.config(bg=COLORS["primary"], fg="#FFFFFF")
            else:
                btn_profile.config(bg=COLORS["card"], fg=COLORS["text"])

            animate_popover()

        # Profile Toggle Button (Top Right Header)
        btn_profile = tk.Button(
            user_bar,
            text=f" 👤 {username} ▾ ",
            font=(FONT, 9, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"],
            activebackground=COLORS["border"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            bd=1,
            highlightbackground=COLORS["border"],
            command=toggle_profile_popover
        )
        btn_profile.pack(side="right")

        tk.Label(
            header,
            text="UTILITIES APPLICATION",
            font=(FONT, 24, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="All-in-one developer & productivity platform",
            font=(FONT, 10),
            fg=COLORS["secondary"],
            bg=COLORS["background"]
        ).pack(anchor="w", pady=(2, 0))

        # Tab Navigation Shell
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        url_tab = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(url_tab, text="  URL Shortener  ")
        URL_Shortening.create_gui(url_tab)

        sms_tab = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(sms_tab, text="  SMS & Email Dispatch  ")
        SMS_and_Email.create_gui(sms_tab)

        fake_tab = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(fake_tab, text="  Fake Data Generator  ")
        FakeDataGeneration.create_gui(fake_tab)

        root.update_idletasks()

    redraw_ui()


if __name__ == "__main__":
    auth.init_user_db()
    root = tk.Tk()
    show_login(root)
    root.mainloop()