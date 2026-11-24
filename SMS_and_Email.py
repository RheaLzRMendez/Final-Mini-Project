"""SMS and email dispatcher with persistent delivery history."""

import json
import os
import queue
import re
import smtplib
import sqlite3
import threading
import tkinter as tk
import uuid
from datetime import datetime
from email.message import EmailMessage
from tkinter import messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from Database import DB_FILE
from SMS_and_Eml_style import COLORS, FONT

try:
    from winotify import Notification as WindowsNotification
except ImportError:
    WindowsNotification = None

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
                            reference_id TEXT NOT NULL UNIQUE,
                            owner_username TEXT NOT NULL DEFAULT '')""")
        columns = {
            row[1] for row in conn.execute(
                "PRAGMA table_info(dispatched_messages)"
            ).fetchall()
        }
        if "owner_username" not in columns:
            conn.execute(
                """ALTER TABLE dispatched_messages
                   ADD COLUMN owner_username TEXT NOT NULL DEFAULT ''"""
            )


def create_gui(parent, username):
    init_message_db()
    frame = tk.Frame(parent, bg=COLORS["background"])

    viewport = tk.Frame(frame, bg=COLORS["background"])
    viewport.pack(fill="both", expand=True)
    canvas = tk.Canvas(
        viewport, bg=COLORS["background"], highlightthickness=0, borderwidth=0
    )
    page_vertical_scrollbar = ttk.Scrollbar(
        viewport, orient="vertical", style="Vertical.TScrollbar", command=canvas.yview
    )
    page_horizontal_scrollbar = ttk.Scrollbar(
        viewport, orient="horizontal", style="Horizontal.TScrollbar", command=canvas.xview
    )
    canvas.configure(
        yscrollcommand=page_vertical_scrollbar.set,
        xscrollcommand=page_horizontal_scrollbar.set
    )
    canvas.grid(row=0, column=0, sticky="nsew")
    page_vertical_scrollbar.grid(row=0, column=1, sticky="ns")
    page_horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
    viewport.rowconfigure(0, weight=1)
    viewport.columnconfigure(0, weight=1)

    page = tk.Frame(canvas, bg=COLORS["background"])
    page_window = canvas.create_window((0, 0), window=page, anchor="nw")

    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def resize_page(event):
        canvas.itemconfigure(page_window, width=max(event.width, 820))
        update_scroll_region()

    page.bind("<Configure>", update_scroll_region)
    canvas.bind("<Configure>", resize_page)

    card = tk.Frame(page, bg=COLORS["card"], padx=28, pady=22,
                    highlightbackground=COLORS["border"], highlightthickness=1)
    card.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        card, text="SMS & Email", font=(FONT, 18, "bold"),
        bg=COLORS["card"], fg=COLORS["text"]
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

    own_recipient_active = {"value": False}

    def get_own_recipient():
        if message_type.get() == "Email":
            return own_email_entry.get().strip()
        return own_number_entry.get().strip()

    def update_own_recipient():
        value = get_own_recipient()
        recipient_entry.delete(0, tk.END)
        if value:
            recipient_entry.insert(0, value)

    def mark_recipient_manual(event=None):
        own_recipient_active["value"] = False

    recipient_entry.bind("<KeyPress>", mark_recipient_manual)
    recipient_entry.bind("<<Paste>>", mark_recipient_manual)
    recipient_entry.bind("<<Cut>>", mark_recipient_manual)

    def fill_own_recipient():
        value = get_own_recipient()
        if not value:
            messagebox.showwarning(
                "Missing Contact", "Enter your own email or number in the preset fields first.",
                parent=frame
            )
            return
        own_recipient_active["value"] = True
        update_own_recipient()

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

    displayed_references = set()
    with sqlite3.connect(DB_FILE) as conn:
        history = conn.execute(
            """SELECT timestamp, channel, recipient, message_content,
                      delivery_status, reference_id
               FROM dispatched_messages
               WHERE owner_username = ?
               ORDER BY id""",
            (username,)
        ).fetchall()
    for record in history:
        timestamp, mode, recipient, content, status, reference = record
        displayed_references.add(reference)
        dispatched_tree.insert(
            "", "end", values=(timestamp, mode, recipient, content, status, reference)
        )
        append_log(timestamp, mode, recipient, content, status, reference)

    def on_type_change(event=None):
        is_sms = message_type.get() == "SMS"
        subject_entry.config(state="disabled" if is_sms else "normal")
        subject_lbl.config(fg=COLORS["secondary"] if is_sms else COLORS["text"])
        if own_recipient_active["value"]:
            update_own_recipient()

    message_type.bind("<<ComboboxSelected>>", on_type_change)
    on_type_change()

    def show_delivery_notification(mode, recipient, subject, body, timestamp):
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

        preview = body.strip()
        if len(preview) > 160:
            preview = preview[:157].rstrip() + "..."
        subject_line = f"Subject: {subject or '(no subject)'}" if mode == "Email" else None
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
        title.config(text=f"Sending {mode.lower()} to {recipient}...")
        notification.deiconify()

        def finish_delivery(success, status):
            if notification.winfo_exists():
                if mode == "SMS":
                    title_text = (
                        f"📱 SMS Sent to {recipient}: {preview}"
                        if success else f"📱 SMS Failed for {recipient}"
                    )
                elif status.startswith("Simulated"):
                    title_text = f"✉️ Email Simulated to {recipient}"
                else:
                    title_text = (
                        f"✉️ Email Delivered to {recipient}"
                        if success else f"✉️ Email Failed for {recipient}"
                    )
                title.config(text=title_text)
                delivery_status.config(
                    text=f"{'Complete ✓' if success else 'Failed'} · Status: {status}",
                    fg=COLORS["success"] if success else COLORS["danger"]
                )
                notification.after(4600, notification.destroy)

        def fade_in(step=0):
            if not notification.winfo_exists():
                return
            alpha = min(1.0, step / 5)
            notification.attributes("-alpha", alpha)
            if alpha < 1:
                notification.after(25, lambda: fade_in(step + 1))

        fade_in()
        return finish_delivery

    def append_system_log(text):
        log_box.config(state="normal")
        log_box.insert(tk.END, f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {text}\n")
        log_box.see(tk.END)
        log_box.config(state="disabled")

    def dispatch_message(mode, recipient, subject, body):
        if mode == "Email":
            sender = os.environ.get("SENDER_GMAIL", "").strip()
            app_password = "".join(os.environ.get("GMAIL_APP_PASSWORD", "").split())
            if not sender or not app_password:
                return (
                    True,
                    "Simulated SMTP (Gmail credentials not configured)",
                    "Real Gmail delivery is not configured. Set SENDER_GMAIL and "
                    "GMAIL_APP_PASSWORD to your Gmail address and 16-character "
                    "Google App Password (Google Account → Security → 2-Step Verification → App passwords)."
                )
            if len(app_password) != 16:
                return (
                    False,
                    "Failed via Gmail SMTP",
                    "GMAIL_APP_PASSWORD must be the 16-character Google App Password."
                )

            try:
                email = EmailMessage()
                email["From"] = sender
                email["To"] = recipient
                email["Subject"] = subject or "(no subject)"
                email.set_content(body)
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
                    smtp.login(sender, app_password)
                    smtp.send_message(email)
            except (smtplib.SMTPException, OSError, ValueError) as error:
                return False, "Failed via Gmail SMTP", str(error)
            return True, "Delivered via Gmail SMTP", ""

        payload = json.dumps({
            "phone_number": recipient,
            "message": body
        }).encode("utf-8")
        request = Request(
            "https://httpbin.org/post",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urlopen(request, timeout=15) as response:
                if not 200 <= response.getcode() < 300:
                    raise URLError(f"Sandbox returned HTTP {response.getcode()}.")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            return False, "Failed via HTTPBin SMS sandbox", str(error)
        return (
            True,
            "POST accepted by HTTPBin sandbox (not a carrier SMS)",
            "SMS payload was posted to https://httpbin.org/post; this endpoint "
            "simulates a carrier request and does not send an actual SMS."
        )

    result_queue = queue.Queue()

    def refresh_history():
        if not frame.winfo_exists():
            return
        try:
            with sqlite3.connect(DB_FILE) as conn:
                records = conn.execute(
                    """SELECT timestamp, channel, recipient, message_content,
                              delivery_status, reference_id
                       FROM dispatched_messages
                       WHERE owner_username = ?
                       ORDER BY id""",
                    (username,)
                ).fetchall()
        except sqlite3.Error as error:
            append_system_log(f"Could not refresh dispatch history: {error}")
        else:
            for record in records:
                timestamp, mode, recipient, content, status, reference = record
                if reference in displayed_references:
                    continue
                displayed_references.add(reference)
                dispatched_tree.insert(
                    "", "end",
                    values=(timestamp, mode, recipient, content, status, reference)
                )
                append_log(timestamp, mode, recipient, content, status, reference)
        frame.after(1000, refresh_history)

    def show_windows_notification(title, body):
        if WindowsNotification is None:
            return "Windows toast unavailable; install winotify. In-app notification shown."
        try:
            WindowsNotification(
                app_id="Utilities Suite",
                title=title,
                msg=body,
                duration="short"
            ).show()
        except (OSError, RuntimeError, ValueError) as error:
            return f"Windows toast failed ({error}); in-app notification shown."
        return ""

    def poll_dispatch_results():
        if not frame.winfo_exists():
            return
        while True:
            try:
                result = result_queue.get_nowait()
            except queue.Empty:
                break

            (mode, recipient, subject, body, content, timestamp, reference,
             success, status, detail, database_error,
             complete_notification) = result
            if database_error:
                append_system_log(f"Could not save dispatch {reference}: {database_error}")
                messagebox.showerror(
                    "History Save Failed",
                    f"The message result could not be saved to the local database:\n"
                    f"{database_error}",
                    parent=frame
                )
            elif reference not in displayed_references:
                displayed_references.add(reference)
                dispatched_tree.insert(
                    "", "end",
                    values=(timestamp, mode, recipient, content, status, reference)
                )
                append_log(timestamp, mode, recipient, content, status, reference)

            if detail:
                append_system_log(detail)
            complete_notification(success, status)
            preview = body.strip()
            if len(preview) > 160:
                preview = preview[:157].rstrip() + "..."
            if success:
                if mode == "SMS":
                    notification_title = f"📱 SMS Sent to {recipient}: {preview}"
                    notification_body = "HTTPBin sandbox accepted the test request; no SMS was sent."
                elif status.startswith("Simulated"):
                    notification_title = f"✉️ Email Simulated to {recipient}"
                    notification_body = f"Subject: {subject or '(no subject)'}"
                else:
                    notification_title = f"✉️ Email Delivered to {recipient}"
                    notification_body = f"Subject: {subject or '(no subject)'}"
                notification_note = show_windows_notification(
                    notification_title, notification_body
                )
                if notification_note:
                    append_system_log(notification_note)
            else:
                messagebox.showerror(
                    "Delivery Failed",
                    f"{status}:\n{detail or 'The remote service rejected the message.'}",
                    parent=frame
                )
            send_button.config(text="Simulate Send", state="normal")
        frame.after(100, poll_dispatch_results)

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
        reference = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        recipient_entry.delete(0, tk.END)
        subject_entry.delete(0, tk.END)
        message_box.delete("1.0", tk.END)
        complete_notification = show_delivery_notification(
            mode, recipient, subject, body, timestamp
        )
        send_button.config(text="Sending...", state="disabled")
        append_system_log(f"Sending {mode} to {recipient}...")

        def worker():
            success, status, detail = dispatch_message(mode, recipient, subject, body)
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute(
                        """INSERT INTO dispatched_messages
                           (timestamp, channel, recipient, message_content,
                            delivery_status, reference_id, owner_username)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            timestamp, mode, recipient, content, status,
                            reference, username
                        )
                    )
                database_error = ""
            except sqlite3.Error as error:
                database_error = str(error)
            result_queue.put((
                mode, recipient, subject, body, content, timestamp, reference,
                success, status, detail, database_error, complete_notification
            ))

        try:
            threading.Thread(target=worker, daemon=True).start()
        except RuntimeError as error:
            send_button.config(text="Simulate Send", state="normal")
            complete_notification(False, "Could not start background delivery")
            append_system_log(f"Could not start dispatch thread: {error}")
            messagebox.showerror(
                "Dispatch Could Not Start", str(error), parent=frame
            )

    send_button = tk.Button(
        left_form, text="Simulate Send", command=send_message,
        font=(FONT, 10, "bold"), bg=COLORS["primary"], fg="white",
        activebackground=COLORS["primary_dark"], activeforeground="white",
        relief="flat", cursor="hand2", padx=22, pady=9
    )
    send_button.pack(anchor="w", pady=(3, 0))

    scroll_tag = f"SMSPageScroll{id(frame)}"

    def scroll_page_vertically(event):
        if isinstance(event.widget, (tk.Text, ttk.Treeview)):
            return None
        units = -int(event.delta / 120)
        canvas.yview_scroll(units or (-1 if event.delta > 0 else 1), "units")
        return "break"

    def scroll_page_horizontally(event):
        units = -int(event.delta / 120)
        canvas.xview_scroll(units or (-1 if event.delta > 0 else 1), "units")
        return "break"

    canvas.bind_class(scroll_tag, "<MouseWheel>", scroll_page_vertically)
    canvas.bind_class(scroll_tag, "<Shift-MouseWheel>", scroll_page_horizontally)

    def apply_scroll_bindings(widget):
        tags = widget.bindtags()
        if scroll_tag not in tags:
            widget.bindtags((scroll_tag,) + tags)
        for child in widget.winfo_children():
            apply_scroll_bindings(child)

    apply_scroll_bindings(frame)

    frame.pack(fill="both", expand=True)
    frame.after(100, poll_dispatch_results)
    frame.after(1000, refresh_history)
    return frame
