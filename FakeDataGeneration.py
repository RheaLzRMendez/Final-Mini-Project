"""
FakeDataGeneration.py - Interactive Calendar Picker & Single Record Modal.
"""

import calendar
import csv
import random
import sqlite3
import tkinter as tk
from datetime import date, timedelta
from tkinter import filedialog, messagebox, ttk

from Database import DB_FILE
from theme_manager import COLORS, FONT

MIN_RECORDS = 10
MAX_RECORDS = 100

FIELDS = [
    ("full_name", "Full Name"),
    ("address", "Address"),
    ("birthdate", "Birthdate"),
    ("mobile_number", "Mobile Number"),
    ("email", "Email Address"),
    ("gender", "Gender"),
    ("username", "Username"),
    ("company", "Company"),
    ("job_title", "Job Title"),
    ("country", "Country"),
]
COLUMNS = [column for column, _ in FIELDS]

GENDER_OPTIONS = ["Male", "Female", "Prefer not to say"]
JOB_OPTIONS = [
    "Student", "N/A", "Software Engineer", "Accountant",
    "Graphic Designer", "Nurse", "Teacher", "Project Manager",
    "Data Analyst", "Sales Associate", "HR Officer"
]
COMPANY_OPTIONS = [
    "N/A", "Bluewave Solutions", "Pinoy Tech Corp.", "Sunrise Logistics",
    "Island Foods Inc.", "Northgate Systems", "BrightPath Learning",
    "Harbor Trading Co.", "Metro Digital"
]
COUNTRY_OPTIONS = [
    "Philippines", "United States", "Japan", "Singapore",
    "Canada", "Australia", "United Kingdom", "N/A"
]

MALE_NAMES = ["Juan", "Jose", "Mark", "Paolo", "Miguel", "Carlo", "Rafael", "Gabriel"]
FEMALE_NAMES = ["Maria", "Ana", "Sofia", "Isabel", "Angela", "Patricia", "Camille"]
LAST_NAMES = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza"]
STREETS = ["Rizal Street", "Mabini Avenue", "Bonifacio Road", "Luna Street"]
CITIES = ["Quezon City", "Manila", "Makati", "Pasig", "Taguig", "Cebu City"]
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com"]
PHONE_PREFIXES = ["0917", "0918", "0927", "0935", "0956"]


def generate_record():
    gender = random.choice(["Male", "Female"])
    first = random.choice(MALE_NAMES if gender == "Male" else FEMALE_NAMES)
    last = random.choice(LAST_NAMES)
    tag = random.randint(10, 999)
    handle = f"{first}{last}".lower().replace(" ", "")

    birthdate = date.today() - timedelta(days=random.randint(18 * 365, 60 * 365))
    address = f"{random.randint(1, 999)} {random.choice(STREETS)}, {random.choice(CITIES)}"
    mobile = random.choice(PHONE_PREFIXES) + "".join(random.choices("0123456789", k=7))

    return (
        f"{first} {last}",
        address,
        birthdate.strftime("%Y-%m-%d"),
        mobile,
        f"{handle}{tag}@{random.choice(EMAIL_DOMAINS)}",
        gender,
        f"{handle}{tag}",
        random.choice([c for c in COMPANY_OPTIONS if c != "N/A"]),
        random.choice([j for j in JOB_OPTIONS if j not in ("N/A", "Student")]),
        random.choice([co for co in COUNTRY_OPTIONS if co != "N/A"]),
    )


def init_table():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS fake_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            full_name TEXT, address TEXT, birthdate TEXT,
                            mobile_number TEXT, email TEXT, gender TEXT,
                            username TEXT, company TEXT, job_title TEXT,
                            country TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")


def save_records(records):
    placeholders = ", ".join(["?"] * len(COLUMNS))
    with sqlite3.connect(DB_FILE) as conn:
        conn.executemany(
            f"INSERT INTO fake_records ({', '.join(COLUMNS)}) VALUES ({placeholders})",
            records
        )


def load_records():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute(
            f"SELECT id, {', '.join(COLUMNS)} FROM fake_records ORDER BY id DESC"
        ).fetchall()


def delete_all_records():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM fake_records")


def create_gui(parent):
    init_table()
    frame = tk.Frame(parent, bg=COLORS["background"])

    card = tk.Frame(frame, bg=COLORS["card"], padx=30, pady=25,
                    highlightbackground=COLORS["border"], highlightthickness=1)
    card.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(card, text="Fake Data Generation", font=(FONT, 18, "bold"),
             bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 4))

    controls = tk.Frame(card, bg=COLORS["card"])
    controls.pack(fill="x", pady=(0, 14))

    tk.Label(controls, text="Batch Count:", font=(FONT, 9, "bold"),
             bg=COLORS["card"], fg=COLORS["text"]).pack(side="left", padx=(0, 8))

    count_var = tk.StringVar(value=str(MIN_RECORDS))
    ttk.Spinbox(controls, from_=MIN_RECORDS, to=MAX_RECORDS, width=5,
                textvariable=count_var, font=(FONT, 9)).pack(side="left", padx=(0, 12))

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)
        records = load_records()
        for rec in records:
            tree.insert("", "end", values=rec[1:])
        status.config(text=f"Total records in database: {len(records)}")

    def handle_generate():
        try:
            count = int(count_var.get())
            if not (MIN_RECORDS <= count <= MAX_RECORDS):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", f"Enter a number between {MIN_RECORDS} and {MAX_RECORDS}.")
            return

        recs = [generate_record() for _ in range(count)]
        save_records(recs)
        refresh_table()
        messagebox.showinfo("Success", f"Generated and stored {count} fake records!")

    # --- FULLY INTERACTIVE DARK GRID CALENDAR PICKER ---
    def open_modern_calendar(target_entry, parent_dialog):
        cal_win = tk.Toplevel(parent_dialog)
        cal_win.title("Select Birthdate")
        cal_win.geometry("340x420")
        cal_win.configure(bg="#18181B")
        cal_win.transient(parent_dialog)
        cal_win.grab_set()

        today = date.today()
        state = {"year": today.year, "month": today.month, "selected_day": today.day}

        header_frame = tk.Frame(cal_win, bg="#18181B", padx=12, pady=12)
        header_frame.pack(fill="x")

        # Interactive Month and Year Selectors
        month_names = list(calendar.month_name)[1:]
        cbo_month = ttk.Combobox(header_frame, values=month_names, width=10, state="readonly", font=(FONT, 9, "bold"))
        cbo_month.set(calendar.month_name[state["month"]])
        cbo_month.pack(side="left", padx=(0, 5))

        years = [str(y) for y in range(today.year - 90, today.year + 1)]
        cbo_year = ttk.Combobox(header_frame, values=years, width=6, state="readonly", font=(FONT, 9, "bold"))
        cbo_year.set(str(state["year"]))
        cbo_year.pack(side="left")

        btn_frame = tk.Frame(header_frame, bg="#18181B")
        btn_frame.pack(side="right")

        grid_frame = tk.Frame(cal_win, bg="#18181B", padx=12, pady=5)
        grid_frame.pack(fill="both", expand=True)

        days_header = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

        def render_calendar():
            for child in grid_frame.winfo_children():
                child.destroy()

            for col_idx, day_name in enumerate(days_header):
                tk.Label(grid_frame, text=day_name, font=(FONT, 9, "bold"),
                         bg="#18181B", fg="#A1A1AA", width=4).grid(row=0, column=col_idx, pady=4)

            cal_matrix = calendar.monthcalendar(state["year"], state["month"])

            for row_idx, week in enumerate(cal_matrix, start=1):
                for col_idx, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid_frame, text="", bg="#18181B", width=4).grid(row=row_idx, column=col_idx, pady=2)
                    else:
                        is_selected = (day == state["selected_day"])
                        btn_bg = "#F87171" if is_selected else "#27272A"
                        btn_fg = "#FFFFFF" if is_selected else "#E4E4E7"

                        def make_cmd(d=day):
                            def select_cmd():
                                state["selected_day"] = d
                                render_calendar()
                            return select_cmd

                        btn_day = tk.Button(
                            grid_frame, text=str(day), font=(FONT, 9, "bold" if is_selected else "normal"),
                            bg=btn_bg, fg=btn_fg, activebackground="#F87171", activeforeground="#FFFFFF",
                            relief="flat", cursor="hand2", width=3, height=1, command=make_cmd(day)
                        )
                        btn_day.grid(row=row_idx, column=col_idx, padx=2, pady=2)

        def on_month_change(event=None):
            state["month"] = month_names.index(cbo_month.get()) + 1
            state["selected_day"] = 1
            render_calendar()

        def on_year_change(event=None):
            state["year"] = int(cbo_year.get())
            state["selected_day"] = 1
            render_calendar()

        cbo_month.bind("<<ComboboxSelected>>", on_month_change)
        cbo_year.bind("<<ComboboxSelected>>", on_year_change)

        def prev_month():
            if state["month"] == 1:
                state["month"] = 12
                state["year"] -= 1
            else:
                state["month"] -= 1
            cbo_month.set(calendar.month_name[state["month"]])
            cbo_year.set(str(state["year"]))
            state["selected_day"] = 1
            render_calendar()

        def next_month():
            if state["month"] == 12:
                state["month"] = 1
                state["year"] += 1
            else:
                state["month"] += 1
            cbo_month.set(calendar.month_name[state["month"]])
            cbo_year.set(str(state["year"]))
            state["selected_day"] = 1
            render_calendar()

        tk.Button(btn_frame, text="▲", command=prev_month, font=(FONT, 8),
                  bg="#27272A", fg="#FFFFFF", relief="flat", width=3, cursor="hand2").pack(side="left", padx=2)
        tk.Button(btn_frame, text="▼", command=next_month, font=(FONT, 8),
                  bg="#27272A", fg="#FFFFFF", relief="flat", width=3, cursor="hand2").pack(side="left", padx=2)

        def confirm_selection():
            formatted = f"{state['year']}-{state['month']:02d}-{state['selected_day']:02d}"
            target_entry.delete(0, tk.END)
            target_entry.insert(0, formatted)
            cal_win.destroy()

        footer_frame = tk.Frame(cal_win, bg="#18181B", pady=12)
        footer_frame.pack(fill="x")
        tk.Button(footer_frame, text="Confirm Date", command=confirm_selection, font=(FONT, 10, "bold"),
                  bg="#F87171", fg="#FFFFFF", relief="flat", cursor="hand2", padx=22, pady=6).pack()

        render_calendar()

    def add_single_record_dialog():
        dialog = tk.Toplevel(parent)
        dialog.title("Add Single Record")
        dialog.geometry("480x680")
        dialog.configure(bg=COLORS["background"])
        dialog.transient(parent)
        dialog.grab_set()

        d_card = tk.Frame(dialog, bg=COLORS["card"], padx=20, pady=20,
                          highlightbackground=COLORS["border"], highlightthickness=1)
        d_card.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(d_card, text="Add Single Record", font=(FONT, 14, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        widgets = {}

        for col, label in FIELDS:
            lbl_frame = tk.Frame(d_card, bg=COLORS["card"])
            lbl_frame.pack(fill="x", pady=2)
            tk.Label(lbl_frame, text=label, font=(FONT, 9, "bold"), bg=COLORS["card"],
                     fg=COLORS["text"], width=13, anchor="w").pack(side="left")

            if col == "gender":
                cbo = ttk.Combobox(lbl_frame, values=GENDER_OPTIONS, state="readonly", font=(FONT, 9))
                cbo.pack(side="right", fill="x", expand=True, padx=(5, 0))
                cbo.set("Male")
                widgets[col] = cbo

            elif col == "job_title":
                cbo = ttk.Combobox(lbl_frame, values=JOB_OPTIONS, state="readonly", font=(FONT, 9))
                cbo.pack(side="right", fill="x", expand=True, padx=(5, 0))
                cbo.set("Student")
                widgets[col] = cbo

            elif col == "company":
                cbo = ttk.Combobox(lbl_frame, values=COMPANY_OPTIONS, state="readonly", font=(FONT, 9))
                cbo.pack(side="right", fill="x", expand=True, padx=(5, 0))
                cbo.set("N/A")
                widgets[col] = cbo

            elif col == "country":
                cbo = ttk.Combobox(lbl_frame, values=COUNTRY_OPTIONS, state="readonly", font=(FONT, 9))
                cbo.pack(side="right", fill="x", expand=True, padx=(5, 0))
                cbo.set("Philippines")
                widgets[col] = cbo

            elif col == "birthdate":
                b_frame = tk.Frame(lbl_frame, bg=COLORS["card"])
                b_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))

                ent = tk.Entry(b_frame, font=(FONT, 9), bg=COLORS["input"], fg=COLORS["text"],
                               relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
                ent.pack(side="left", fill="x", expand=True, ipady=3)
                ent.insert(0, date.today().strftime("%Y-%m-%d"))

                btn_cal = tk.Button(b_frame, text="📅 Calendar", command=lambda target=ent: open_modern_calendar(target, dialog),
                                    font=(FONT, 8, "bold"), bg=COLORS["input"], fg=COLORS["primary_dark"],
                                    relief="flat", cursor="hand2")
                btn_cal.pack(side="right", padx=(4, 0))
                widgets[col] = ent

            else:
                ent = tk.Entry(lbl_frame, font=(FONT, 9), bg=COLORS["input"], fg=COLORS["text"],
                               relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
                ent.pack(side="right", fill="x", expand=True, padx=(5, 0), ipady=3)
                widgets[col] = ent

        def autofill():
            fake = generate_record()
            for (col, _), val in zip(FIELDS, fake):
                w = widgets[col]
                if isinstance(w, ttk.Combobox):
                    w.set(val)
                else:
                    w.delete(0, tk.END)
                    w.insert(0, val)

        def save_single():
            row_data = [widgets[col].get().strip() for col, _ in FIELDS]
            if not any(row_data):
                messagebox.showwarning("Empty Form", "Please fill in at least one field.", parent=dialog)
                return
            save_records([tuple(row_data)])
            refresh_table()
            dialog.destroy()
            messagebox.showinfo("Saved", "Record added successfully!")

        btn_box = tk.Frame(d_card, bg=COLORS["card"])
        btn_box.pack(fill="x", pady=(15, 0))

        tk.Button(btn_box, text="Auto-Fill Fake Data", command=autofill, font=(FONT, 9, "bold"),
                  bg=COLORS["input"], fg=COLORS["primary_dark"], relief="flat", cursor="hand2", padx=10, pady=6).pack(side="left")

        tk.Button(btn_box, text="Save Record", command=save_single, font=(FONT, 9, "bold"),
                  bg=COLORS["primary"], fg="white", relief="flat", cursor="hand2", padx=16, pady=6).pack(side="right")

    def handle_clear():
        if messagebox.askyesno("Confirm", "Delete all stored fake records?"):
            delete_all_records()
            refresh_table()

    def handle_export():
        records = load_records()
        if not records:
            messagebox.showinfo("No Data", "There are no records to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filepath:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([label for _, label in FIELDS])
                for rec in records:
                    writer.writerow(rec[1:])
            messagebox.showinfo("Exported", "Data exported successfully!")

    def make_button(text, command, primary=False):
        btn = tk.Button(
            controls, text=text, command=command, font=(FONT, 9, "bold"),
            bg=COLORS["primary"] if primary else COLORS["input"],
            fg="white" if primary else COLORS["primary_dark"],
            activebackground=COLORS["primary_dark"] if primary else COLORS["border"],
            activeforeground="white" if primary else COLORS["text"],
            relief="flat", cursor="hand2", padx=14, pady=6
        )
        btn.pack(side="left", padx=(0, 6))
        return btn

    make_button("Batch Generate", handle_generate, primary=True)
    make_button("+ Add Single Record", add_single_record_dialog)
    make_button("Export CSV", handle_export)
    make_button("Clear Records", handle_clear)

    table_frame = tk.Frame(card, bg=COLORS["card"])
    table_frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.configure("FDG.Treeview", rowheight=26, font=(FONT, 9),
                    background=COLORS["input"], fieldbackground=COLORS["input"],
                    foreground=COLORS["text"])
    style.configure("FDG.Treeview.Heading", font=(FONT, 9, "bold"),
                    background=COLORS["light"], foreground=COLORS["text"])

    tree = ttk.Treeview(table_frame, style="FDG.Treeview", columns=COLUMNS, show="headings", height=11)
    widths = {"full_name": 140, "address": 220, "birthdate": 90, "mobile_number": 110,
              "email": 210, "gender": 70, "username": 130, "company": 150,
              "job_title": 150, "country": 110}

    for column, label in FIELDS:
        tree.heading(column, text=label)
        tree.column(column, width=widths[column], minwidth=70, anchor="w")

    y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)
    tree.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")

    status = tk.Label(card, text="", font=(FONT, 9), bg=COLORS["card"], fg=COLORS["secondary"])
    status.pack(anchor="w", pady=(10, 0))

    refresh_table()
    frame.pack(fill="both", expand=True)
    return frame