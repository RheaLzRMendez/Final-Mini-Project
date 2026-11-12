"""
Login.py - Login and Sign Up screen interfaces built inside Tkinter.
"""

import tkinter as tk
import auth

COLORS = {
    "background": "#EAF3FF",
    "card": "#FFFFFF",
    "primary": "#5B9BD5",
    "dark": "#193B63",
    "secondary": "#718096",
    "input": "#F7FAFF",
    "border": "#D5E3F2",
    "error": "#C0392B",
    "success": "#2F855A",
}
FONT = "Arial"


def center_window(root, width, height):
    """Sizes the window and centers it on screen."""
    width = min(width, root.winfo_screenwidth() - 40)
    height = min(height, root.winfo_screenheight() - 80)
    x = (root.winfo_screenwidth() - width) // 2
    y = max((root.winfo_screenheight() - height) // 2 - 20, 0)
    root.geometry(f"{width}x{height}+{x}+{y}")


def make_card(root, title):
    """Resets window content and builds the modern white card wrapper."""
    for widget in root.winfo_children():
        widget.destroy()

    root.title(title)
    center_window(root, 1000, 780)
    root.configure(bg=COLORS["background"])

    container = tk.Frame(root, bg=COLORS["background"])
    container.pack(expand=True, fill="both")

    card = tk.Frame(container, bg=COLORS["card"], padx=55, pady=45,
                    highlightbackground=COLORS["border"], highlightthickness=1)
    card.place(relx=0.5, rely=0.5, anchor="center", width=480)
    return card


def add_heading(card, subtitle, gap=30):
    tk.Label(card, text="UTILITIES APPLICATION", font=(FONT, 21, "bold"),
             fg=COLORS["dark"], bg=COLORS["card"]).pack(pady=(5, 8))
    tk.Label(card, text=subtitle, font=(FONT, 11),
             fg=COLORS["secondary"], bg=COLORS["card"]).pack(pady=(0, gap))


def add_field(card, label, show="", gap=20):
    tk.Label(card, text=label, font=(FONT, 10, "bold"), fg=COLORS["dark"],
             bg=COLORS["card"], anchor="w").pack(fill="x", pady=(0, 7))
    entry = tk.Entry(card, font=(FONT, 11), bg=COLORS["input"], fg=COLORS["dark"],
                     relief="solid", bd=1, show=show)
    entry.pack(fill="x", ipady=10, pady=(0, gap))
    return entry


def add_show_password(card, *entries):
    show_var = tk.BooleanVar()

    def toggle():
        for entry in entries:
            entry.config(show="" if show_var.get() else "*")

    tk.Checkbutton(card, text="Show password", variable=show_var, command=toggle,
                   font=(FONT, 10), fg=COLORS["secondary"], bg=COLORS["card"],
                   activebackground=COLORS["card"], activeforeground=COLORS["dark"],
                   bd=0, highlightthickness=0, cursor="hand2").pack(anchor="w")


def add_message(card):
    label = tk.Label(card, text="", font=(FONT, 10), fg=COLORS["error"],
                     bg=COLORS["card"], wraplength=370, justify="left", anchor="w")
    label.pack(fill="x", pady=(10, 0))
    return label


def say(label, text, ok=False):
    label.config(text=text, fg=COLORS["success"] if ok else COLORS["error"])


def add_button(card, text, command):
    tk.Button(card, text=text, font=(FONT, 11, "bold"), bg=COLORS["primary"],
              fg="white", activebackground=COLORS["dark"], activeforeground="white",
              relief="flat", cursor="hand2", command=command
              ).pack(fill="x", ipady=10, pady=(18, 0))


def add_link(card, text, command):
    link = tk.Label(card, text=text, font=(FONT, 10), fg=COLORS["primary"],
                    bg=COLORS["card"], cursor="hand2")
    link.pack(pady=(22, 5))
    link.bind("<Button-1>", lambda event: command())


def create_login(root, on_login, prefill="", notice=""):
    card = make_card(root, "Utilities Application - Login")
    add_heading(card, "Welcome back! Please log in.")

    identifier_entry = add_field(card, "Email or Username")
    password_entry = add_field(card, "Password", show="*", gap=10)
    add_show_password(card, password_entry)
    message = add_message(card)
    if notice:
        say(message, notice, ok=True)

    def attempt_login(event=None):
        identifier = identifier_entry.get().strip()
        password = password_entry.get()
        if not identifier or not password:
            return say(message, "Enter your email or username and your password.")
        username = auth.verify_login(identifier, password)
        if username is None:
            return say(message, "Wrong username/email or password.")
        on_login(username)

    add_button(card, "LOG IN", attempt_login)
    add_link(card, "Don't have an account? Sign Up",
             lambda: create_signup(root, on_login))

    identifier_entry.bind("<Return>", attempt_login)
    password_entry.bind("<Return>", attempt_login)
    if prefill:
        identifier_entry.insert(0, prefill)
        password_entry.focus()
    else:
        identifier_entry.focus()


def create_signup(root, on_login):
    card = make_card(root, "Utilities Application - Sign Up")
    add_heading(card, "Create an account to get started.", gap=22)

    username_entry = add_field(card, "Username", gap=14)
    email_entry = add_field(card, "Email", gap=14)
    password_entry = add_field(card, "Password (at least 8 characters)", show="*", gap=14)
    confirm_entry = add_field(card, "Confirm password", show="*", gap=10)
    add_show_password(card, password_entry, confirm_entry)
    message = add_message(card)

    def attempt_signup(event=None):
        ok, text = auth.register_user(username_entry.get(), email_entry.get(),
                                      password_entry.get(), confirm_entry.get())
        if ok:
            create_login(root, on_login, prefill=username_entry.get().strip(), notice=text)
        else:
            say(message, text)

    add_button(card, "CREATE ACCOUNT", attempt_signup)
    add_link(card, "Already have an account? Log In",
             lambda: create_login(root, on_login))

    for entry in (username_entry, email_entry, password_entry, confirm_entry):
        entry.bind("<Return>", attempt_signup)
    username_entry.focus()