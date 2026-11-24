"""Offline SMS and email dispatcher with persistent simulated delivery history."""

import re
import sqlite3
import tkinter as tk
import uuid
from datetime import datetime
from tkinter import messagebox, ttk

from Database import DB_FILE
from SMS_and_Eml_style import COLORS, FONT

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)
PHONE_PATTERN = re.compile(r"^\+?[0-9](?:[0-9 ().-]*[0-9])$")


def is_valid_email_recipient(recipient):
    return bool(EMAIL_PATTERN.fullmatch(recipient))


def is_valid_sms_recipient(recipient):
    digits = re.sub(r"\D", "", recipient)
    return bool(PHONE_PATTERN.fullmatch(recipient)) and 7 <= len(digits) <= 15


def init_message_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS dispatched_messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            channel TEXT NOT NULL,
                            recipient TEXT NOT NULL,
                            message_content TEXT NOT NULL,
                            delivery_status TEXT NOT NULL,
                            reference_id TEXT NOT NULL UNIQUE)""")


def create_gui(parent, own_email=""):
    init_message_db()
    frame = tk.Frame(parent, bg=COLORS["background"])

    card = tk.Frame(frame, bg=COLORS["card"], padx=28, pady=22,
                    highlightbackground=COLORS["border"], highlightthickness=1)
    card.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        card, text="SMS & Email Dispatcher", font=(FONT, 18, "bold"),
        bg=COLORS["card"], fg=COLORS["text"]
    ).pack(anchor="w", pady=(0, 4))

    tk.Label(
        card, text="Simulation mode — messages are recorded locally and never sent.",
        font=(FONT, 10), bg=COLORS["card"], fg=COLORS["secondary"]
    ).pack(anchor="w", pady=(0, 14))

    content_split = tk.Frame(card, bg=COLORS["card"])
    content_split.pack(fill="both", expand=True)
    left_form = tk.Frame(content_split, bg=COLORS["card"])
    left_form.pack(side="left", fill="both", expand=True, padx=(0, 18))
    right_panel = tk.Frame(content_split, bg=COLORS["card"])
    right_panel.pack(side="right", fill="both", expand=True)

    def add_label(parent_widget, text):
        tk.Label(parent_widget, text=text, font=(FONT, 9, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(7, 3))

    add_label(left_form, "Message Channel")
    message_type = ttk.Combobox(
        left_form, values=["Email", "SMS"], state="readonly", font=(FONT, 10)
    )
    message_type.pack(fill="x", ipady=4)
    message_type.set("Email")

    add_label(left_form, "Recipient")
    recipient_entry = tk.Entry(
        left_form, font=(FONT, 10), bg=COLORS["input"], relief="flat",
        highlightthickness=1, highlightbackground=COLORS["border"]
    )
    recipient_entry.pack(fill="x", ipady=7)

    preset_frame = tk.Frame(left_form, bg=COLORS["card"])
    preset_frame.pack(fill="x", pady=(5, 0))
    tk.Label(preset_frame, text="My Number", font=(FONT, 8),
             bg=COLORS["card"], fg=COLORS["secondary"]).pack(side="left")
    own_number_entry = tk.Entry(
        preset_frame, font=(FONT, 9), bg=COLORS["input"], relief="flat",
        highlightthickness=1, highlightbackground=COLORS["border"]
    )
    own_number_entry.pack(side="left", fill="x", expand=True, padx=(5, 10), ipady=4)
    tk.Label(preset_frame, text="My Email", font=(FONT, 8),
             bg=COLORS["card"], fg=COLORS["secondary"]).pack(side="left")
    own_email_entry = tk.Entry(
        preset_frame, font=(FONT, 9), bg=COLORS["input"], relief="flat",
        highlightthickness=1, highlightbackground=COLORS["border"]
    )
    own_email_entry.pack(side="left", fill="x", expand=True, padx=(5, 0), ipady=4)
    own_email_entry.insert(0, own_email)

    def fill_own_recipient():
        value = own_email_entry.get().strip() if message_type.get() == "Email" else own_number_entry.get().strip()
        if not value:
            messagebox.showwarning(
                "Missing Contact", "Enter your own email or number in the preset fields first.",
                parent=frame
            )
            return
        recipient_entry.delete(0, tk.END)
        recipient_entry.insert(0, value)

    tk.Button(
        left_form, text="My Own Number / Email", command=fill_own_recipient,
        font=(FONT, 8, "bold"), bg=COLORS["input"], fg=COLORS["text"],
        relief="flat", cursor="hand2", padx=8, pady=5
    ).pack(anchor="w", pady=(5, 0))

    subject_lbl = tk.Label(left_form, text="Subject", font=(FONT, 9, "bold"),
                           bg=COLORS["card"], fg=COLORS["text"])
    subject_lbl.pack(anchor="w", pady=(9, 3))
    subject_entry = tk.Entry(
        left_form, font=(FONT, 10), bg=COLORS["input"], relief="flat",
        highlightthickness=1, highlightbackground=COLORS["border"]
    )
    subject_entry.pack(fill="x", ipady=7)

    add_label(left_form, "Message Payload")
    payload_frame = tk.Frame(left_form, bg=COLORS["card"])
    payload_frame.pack(fill="both", expand=True, pady=(2, 10))
    message_box = tk.Text(
        payload_frame, height=6, font=(FONT, 10), bg=COLORS["input"],
        fg=COLORS["text"], relief="flat", highlightthickness=1,
        highlightbackground=COLORS["border"]
    )
    payload_scrollbar = ttk.Scrollbar(
        payload_frame, orient="vertical", style="Vertical.TScrollbar",
        command=message_box.yview
    )
    message_box.configure(yscrollcommand=payload_scrollbar.set)
    message_box.pack(side="left", fill="both", expand=True)
    payload_scrollbar.pack(side="right", fill="y")

    add_label(right_panel, "Dispatched Messages")
    columns = ("timestamp", "channel", "recipient", "message_content", "status", "reference")
    history_frame = tk.Frame(right_panel, bg=COLORS["card"])
    history_frame.pack(fill="both", expand=True)
    dispatched_tree = ttk.Treeview(
        history_frame, columns=columns, show="headings", height=7
    )
    for column, title, width in (
        ("timestamp", "Timestamp", 130), ("channel", "Channel", 65),
        ("recipient", "Recipient", 130), ("message_content", "Message Content", 220),
        ("status", "Status", 150),
        ("reference", "Reference ID", 145),
    ):
        dispatched_tree.heading(column, text=title)
        dispatched_tree.column(column, width=width, minwidth=60, anchor="w")
    history_y_scroll = ttk.Scrollbar(
        history_frame, orient="vertical", style="Vertical.TScrollbar",
        command=dispatched_tree.yview
    )
    history_x_scroll = ttk.Scrollbar(
        history_frame, orient="horizontal", style="Horizontal.TScrollbar",
        command=dispatched_tree.xview
    )
    dispatched_tree.configure(
        yscrollcommand=history_y_scroll.set,
        xscrollcommand=history_x_scroll.set
    )
    history_frame.rowconfigure(0, weight=1)
    history_frame.columnconfigure(0, weight=1)
    dispatched_tree.grid(row=0, column=0, sticky="nsew")
    history_y_scroll.grid(row=0, column=1, sticky="ns")
    history_x_scroll.grid(row=1, column=0, sticky="ew")

    add_label(right_panel, "Live Log Console")
    log_frame = tk.Frame(right_panel, bg=COLORS["card"])
    log_frame.pack(fill="both", expand=True, pady=2)
    log_box = tk.Text(
        log_frame, height=9, font=("Consolas", 9), bg="#0F172A",
        fg="#38BDF8", relief="flat", state="disabled", padx=10, pady=8
    )
    log_scrollbar = ttk.Scrollbar(
        log_frame, orient="vertical", style="Vertical.TScrollbar",
        command=log_box.yview
    )
    log_box.configure(yscrollcommand=log_scrollbar.set)
    log_frame.rowconfigure(0, weight=1)
    log_frame.columnconfigure(0, weight=1)
    log_box.grid(row=0, column=0, sticky="nsew")
    log_scrollbar.grid(row=0, column=1, sticky="ns")

    def append_log(timestamp, mode, recipient, content, status, reference):
        log_text = (
            f"[{timestamp}] [{mode.upper()} {status}]\n"
            f"To: {recipient}\nMessage: {content}\n"
            f"Reference: {reference}\n{'-' * 45}\n"
        )
        log_box.config(state="normal")
        log_box.insert(tk.END, log_text)
        log_box.see(tk.END)
        log_box.config(state="disabled")

    with sqlite3.connect(DB_FILE) as conn:
        history = conn.execute(
            """SELECT timestamp, channel, recipient, message_content,
                      delivery_status, reference_id
               FROM dispatched_messages ORDER BY id"""
        ).fetchall()
    for record in history:
        timestamp, mode, recipient, content, status, reference = record
        dispatched_tree.insert(
            "", "end", values=(timestamp, mode, recipient, content, status, reference)
        )
        append_log(timestamp, mode, recipient, content, status, reference)

    def on_type_change(event=None):
        is_sms = message_type.get() == "SMS"
        subject_entry.config(state="disabled" if is_sms else "normal")
        subject_lbl.config(fg=COLORS["secondary"] if is_sms else COLORS["text"])

    message_type.bind("<<ComboboxSelected>>", on_type_change)
    on_type_change()

    def show_delivery_notification(mode, recipient, subject, body, timestamp, status):
        parent_window = frame.winfo_toplevel()
        notification = tk.Toplevel(parent_window)
        notification.withdraw()
        notification.overrideredirect(True)
        notification.transient(parent_window)
        notification.configure(bg=COLORS["border"])
        notification.attributes("-alpha", 0.0)

        width = min(390, max(280, parent_window.winfo_width() - 32))
        card = tk.Frame(
            notification, bg=COLORS["card"], padx=16, pady=14,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        card.pack(fill="both", expand=True)

        heading = tk.Frame(card, bg=COLORS["card"])
        heading.pack(fill="x")
        title = tk.Label(
            heading, text="", font=(FONT, 10, "bold"),
            bg=COLORS["card"], fg=COLORS["text"],
            wraplength=width - 72, justify="left", anchor="w"
        )
        title.pack(side="left", fill="x", expand=True)
        tk.Button(
            heading, text="×", command=notification.destroy,
            font=(FONT, 12, "bold"), bg=COLORS["card"], fg=COLORS["secondary"],
            activebackground=COLORS["input"], activeforeground=COLORS["text"],
            relief="flat", cursor="hand2", padx=5, pady=0
        ).pack(side="right", anchor="n")

        if mode == "SMS":
            delivered_title = f"📱 SMS Delivered to {recipient}"
            sending_title = f"Sending SMS to {recipient}..."
            subject_line = None
        else:
            delivered_title = f"✉️ Email Sent to {recipient}"
            sending_title = f"Sending email to {recipient}..."
            subject_line = f"Subject: {subject or '(no subject)'}"

        preview = body.strip()
        if len(preview) > 160:
            preview = preview[:157].rstrip() + "..."
        if subject_line:
            tk.Label(
                card, text=subject_line, font=(FONT, 9, "bold"),
                bg=COLORS["card"], fg=COLORS["text"],
                wraplength=width - 36, justify="left", anchor="w"
            ).pack(fill="x", anchor="w", pady=(8, 3))
        tk.Label(
            card, text=preview, font=(FONT, 9), bg=COLORS["card"],
            fg=COLORS["secondary"], wraplength=width - 36,
            justify="left", anchor="w"
        ).pack(fill="x", anchor="w", pady=(8 if not subject_line else 0, 5))
        tk.Label(
            card, text=f"Sent: {timestamp}", font=(FONT, 8),
            bg=COLORS["card"], fg=COLORS["secondary"], anchor="w"
        ).pack(fill="x", pady=(2, 5))
        delivery_status = tk.Label(
            card, text="Sending...", font=(FONT, 9, "bold"),
            bg=COLORS["card"], fg=COLORS["primary"], anchor="w"
        )
        delivery_status.pack(fill="x")

        notification.update_idletasks()
        height = notification.winfo_reqheight()
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        x = parent_x + max(8, parent_window.winfo_width() - width - 16)
        y = parent_y + max(8, parent_window.winfo_height() - height - 16)
        notification.geometry(f"{width}x{height}+{x}+{y}")
        title.config(text=sending_title)
        notification.deiconify()

        def finish_delivery():
            if notification.winfo_exists():
                title.config(text=delivered_title)
                delivery_status.config(
                    text=f"Delivered ✓ · Status: {status}",
                    fg=COLORS["success"]
                )

        def fade_in(step=0):
            if not notification.winfo_exists():
                return
            alpha = min(1.0, step / 5)
            notification.attributes("-alpha", alpha)
            if alpha < 1:
                notification.after(25, lambda: fade_in(step + 1))

        notification.after(350, finish_delivery)
        notification.after(4600, notification.destroy)
        fade_in()

    def send_message():
        mode = message_type.get()
        recipient = recipient_entry.get().strip()
        subject = subject_entry.get().strip() if mode == "Email" else ""
        body = message_box.get("1.0", tk.END).strip()
        if not recipient or not body:
            messagebox.showwarning(
                "Missing Fields", "Please enter a recipient and message body.", parent=frame
            )
            return

        if mode == "SMS" and not is_valid_sms_recipient(recipient):
            messagebox.showwarning(
                "Invalid SMS Recipient",
                "Enter a valid phone number for SMS (7 to 15 digits, with an optional leading +).",
                parent=frame
            )
            return
        if mode == "Email" and not is_valid_email_recipient(recipient):
            messagebox.showwarning(
                "Invalid Email Recipient",
                "Enter a valid email address for email delivery.",
                parent=frame
            )
            return

        content = f"Subject: {subject}\n\n{body}" if subject else body
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = (
            "Delivered via Simulated Carrier"
            if mode == "SMS" else "Dispatched via Simulated SMTP"
        )
        reference = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                """INSERT INTO dispatched_messages
                   (timestamp, channel, recipient, message_content, delivery_status, reference_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (timestamp, mode, recipient, content, status, reference)
            )

        dispatched_tree.insert(
            "", "end", values=(timestamp, mode, recipient, content, status, reference)
        )
        append_log(timestamp, mode, recipient, content, status, reference)
        recipient_entry.delete(0, tk.END)
        subject_entry.delete(0, tk.END)
        message_box.delete("1.0", tk.END)
        show_delivery_notification(mode, recipient, subject, body, timestamp, status)

    tk.Button(
        left_form, text="Simulate Send", command=send_message,
        font=(FONT, 10, "bold"), bg=COLORS["primary"], fg="white",
        activebackground=COLORS["primary_dark"], activeforeground="white",
        relief="flat", cursor="hand2", padx=22, pady=9
    ).pack(anchor="w", pady=(3, 0))

    frame.pack(fill="both", expand=True)
    return frame
