"""
SMS_and_Email.py - Modernized SMS & Email Dispatcher
"""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from SMS_and_Eml_style import COLORS, FONT


def create_gui(parent):
    frame = tk.Frame(parent, bg=COLORS["background"])

    card = tk.Frame(frame, bg=COLORS["card"], padx=35, pady=25,
                    highlightbackground=COLORS["border"], highlightthickness=1)
    card.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        card, text="SMS & Email Dispatcher", font=(FONT, 18, "bold"),
        bg=COLORS["card"], fg=COLORS["text"]
    ).pack(anchor="w", pady=(0, 4))

    tk.Label(
        card, text="Compose and dispatch messages to recipients with live log tracking.",
        font=(FONT, 10), bg=COLORS["card"], fg=COLORS["secondary"]
    ).pack(anchor="w", pady=(0, 18))

    content_split = tk.Frame(card, bg=COLORS["card"])
    content_split.pack(fill="both", expand=True)

    left_form = tk.Frame(content_split, bg=COLORS["card"])
    left_form.pack(side="left", fill="both", expand=True, padx=(0, 20))

    right_log = tk.Frame(content_split, bg=COLORS["card"])
    right_log.pack(side="right", fill="both", expand=True)

    def add_label(parent_widget, text):
        lbl = tk.Label(parent_widget, text=text, font=(FONT, 9, "bold"),
                       bg=COLORS["card"], fg=COLORS["text"])
        lbl.pack(anchor="w", pady=(8, 4))
        return lbl

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

    subject_lbl = add_label(left_form, "Subject")
    subject_entry = tk.Entry(
        left_form, font=(FONT, 10), bg=COLORS["input"], relief="flat",
        highlightthickness=1, highlightbackground=COLORS["border"]
    )
    subject_entry.pack(fill="x", ipady=7)

    add_label(left_form, "Message Payload")
    message_box = tk.Text(
        left_form, height=5, font=(FONT, 10), bg=COLORS["input"],
        fg=COLORS["text"], relief="flat", highlightthickness=1,
        highlightbackground=COLORS["border"]
    )
    message_box.pack(fill="x", pady=(2, 12))

    add_label(right_log, "Transmission Log Console")
    log_box = tk.Text(
        right_log, height=14, font=("Consolas", 9), bg="#0F172A",
        fg="#38BDF8", relief="flat", state="disabled", padx=10, pady=10
    )
    log_box.pack(fill="both", expand=True, pady=2)

    def on_type_change(event=None):
        if message_type.get() == "SMS":
            subject_entry.config(state="disabled")
            subject_lbl.config(fg=COLORS["secondary"])
        else:
            subject_entry.config(state="normal")
            subject_lbl.config(fg=COLORS["text"])

    message_type.bind("<<ComboboxSelected>>", on_type_change)

    def send_message():
        mode = message_type.get()
        recipient = recipient_entry.get().strip()
        subject = subject_entry.get().strip()
        body = message_box.get("1.0", tk.END).strip()

        if not recipient or not body:
            messagebox.showwarning("Missing Fields", "Please enter a recipient and message body.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_text = f"[{timestamp}] [{mode.upper()} DISPATCH SUCCESS]\nTo: {recipient}\n"
        if mode == "Email":
            log_text += f"Subject: {subject}\n"
        log_text += f"Message: {body}\n" + ("-" * 45) + "\n"

        log_box.config(state="normal")
        log_box.insert(tk.END, log_text)
        log_box.see(tk.END)
        log_box.config(state="disabled")

        recipient_entry.delete(0, tk.END)
        subject_entry.delete(0, tk.END)
        message_box.delete("1.0", tk.END)
        messagebox.showinfo("Success", f"{mode} message dispatched successfully!")

    send_btn = tk.Button(
        left_form, text="Send Message", command=send_message,
        font=(FONT, 10, "bold"), bg=COLORS["primary"], fg="white",
        activebackground=COLORS["primary_dark"], activeforeground="white",
        relief="flat", cursor="hand2", padx=22, pady=9
    )
    send_btn.pack(anchor="w", pady=(5, 0))

    frame.pack(fill="both", expand=True)
    return frame