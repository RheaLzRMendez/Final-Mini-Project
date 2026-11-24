"""
Customizable batch fake-data generator.
"""

import calendar
import csv
import random
import sqlite3
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from Database import DB_FILE
from theme_manager import COLORS, FONT

MIN_RECORDS = 10
MAX_RECORDS = 100

FIELDS = [
    ("first_name", "First Name"),
    ("last_name", "Last Name"),
    ("age", "Age"),
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
FIELD_LABELS = dict(FIELDS)

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


def generate_record(selected_columns=None):
    gender = random.choice(["Male", "Female"])
    first = random.choice(MALE_NAMES if gender == "Male" else FEMALE_NAMES)
    last = random.choice(LAST_NAMES)
    tag = random.randint(10, 999)
    handle = f"{first}{last}".lower().replace(" ", "")

    age = random.randint(18, 60)
    today = date.today()
    year = today.year - age
    day = min(today.day, calendar.monthrange(year, today.month)[1])
    birthdate = date(year, today.month, day)
    address = f"{random.randint(1, 999)} {random.choice(STREETS)}, {random.choice(CITIES)}"
    mobile = random.choice(PHONE_PREFIXES) + "".join(random.choices("0123456789", k=7))

    record = {
        "first_name": first,
        "last_name": last,
        "age": age,
        "address": address,
        "birthdate": birthdate.strftime("%Y-%m-%d"),
        "mobile_number": mobile,
        "email": f"{handle}{tag}@{random.choice(EMAIL_DOMAINS)}",
        "gender": gender,
        "username": f"{handle}{tag}",
        "company": random.choice([c for c in COMPANY_OPTIONS if c != "N/A"]),
        "job_title": random.choice([j for j in JOB_OPTIONS if j not in ("N/A", "Student")]),
        "country": random.choice([co for co in COUNTRY_OPTIONS if co != "N/A"]),
    }
    return record if selected_columns is None else {
        column: record[column] for column in selected_columns
    }


def init_table():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS fake_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            full_name TEXT, first_name TEXT, last_name TEXT, age INTEGER,
                            address TEXT, birthdate TEXT,
                            mobile_number TEXT, email TEXT, gender TEXT,
                            username TEXT, company TEXT, job_title TEXT,
                            country TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        existing = {row[1] for row in conn.execute("PRAGMA table_info(fake_records)")}
        migrate_full_names = "full_name" in existing and "first_name" not in existing
        for column, sql_type in (
            ("first_name", "TEXT"), ("last_name", "TEXT"), ("age", "INTEGER")
        ):
            if column not in existing:
                conn.execute(f"ALTER TABLE fake_records ADD COLUMN {column} {sql_type}")
        if migrate_full_names:
            conn.execute("""UPDATE fake_records
                            SET first_name = CASE
                                WHEN instr(trim(full_name), ' ') > 0
                                THEN substr(trim(full_name), 1, instr(trim(full_name), ' ') - 1)
                                ELSE trim(full_name)
                            END,
                            last_name = CASE
                                WHEN instr(trim(full_name), ' ') > 0
                                THEN trim(substr(trim(full_name), instr(trim(full_name), ' ') + 1))
                                ELSE ''
                            END,
                            age = CASE WHEN birthdate IS NOT NULL THEN
                                CAST(strftime('%Y', 'now') - strftime('%Y', birthdate)
                                     - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate))
                                     AS INTEGER)
                                ELSE NULL END
                            WHERE full_name IS NOT NULL""")


def save_records(records, selected_columns=None):
    selected_columns = selected_columns or COLUMNS
    placeholders = ", ".join(["?"] * len(selected_columns))
    with sqlite3.connect(DB_FILE) as conn:
        conn.executemany(
            f"INSERT INTO fake_records ({', '.join(selected_columns)}) VALUES ({placeholders})",
            [tuple(record.get(column) for column in selected_columns) for record in records]
        )


def load_records(selected_columns=None):
    if selected_columns is None:
        selected_columns = COLUMNS
    if not selected_columns:
        return []
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute(
            f"SELECT id, {', '.join(selected_columns)} FROM fake_records ORDER BY id DESC"
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

    field_vars = {
        column: tk.BooleanVar(value=False) for column in COLUMNS
    }
    field_frame = tk.LabelFrame(
        card, text="Columns to generate, preview, and export",
        font=(FONT, 9, "bold"), bg=COLORS["card"], fg=COLORS["text"],
        padx=8, pady=4
    )
    field_frame.pack(fill="x", pady=(0, 10))
    inner_frame = tk.Frame(field_frame, bg=COLORS["card"])
    inner_frame.pack(fill="x", expand=True, padx=20, pady=12)
    for column in range(4):
        inner_frame.grid_columnconfigure(column, weight=1, uniform="col_group")

    field_buttons = {}

    def update_field_button(column):
        selected = field_vars[column].get()
        background = COLORS["primary"] if selected else COLORS["toggle_inactive"]
        foreground = "#FFFFFF" if selected else COLORS["toggle_inactive_text"]
        field_buttons[column].configure(
            bg=background, fg=foreground,
            activebackground=background, activeforeground=foreground
        )

    def toggle_field(column):
        field_vars[column].set(not field_vars[column].get())
        update_field_button(column)
        refresh_table()

    for index, (column, label) in enumerate(FIELDS):
        button = tk.Button(
            inner_frame, text=label, font=(FONT, 8, "bold"),
            relief="flat", cursor="hand2",
            command=lambda selected=column: toggle_field(selected)
        )
        field_buttons[column] = button
        update_field_button(column)
        button.grid(
            row=index // 4, column=index % 4, sticky="ew",
            padx=10, pady=8, ipady=6
        )

    def selected_columns():
        return [column for column in COLUMNS if field_vars[column].get()]

    sort_state = {"column": None, "reverse": False}

    def sort_rows(column, reverse):
        rows = [(tree.set(item, column), item) for item in tree.get_children("")]
        try:
            rows.sort(key=lambda pair: int(pair[0]) if column == "age" else pair[0].casefold(),
                      reverse=reverse)
        except ValueError:
            rows.sort(key=lambda pair: pair[0].casefold(), reverse=reverse)
        for index, (_, item) in enumerate(rows):
            tree.move(item, "", index)
        update_headings()

    def sort_by_column(column):
        if sort_state["column"] == column:
            sort_state["reverse"] = not sort_state["reverse"]
        else:
            sort_state["column"] = column
            sort_state["reverse"] = False
        sort_rows(column, sort_state["reverse"])

    def update_headings():
        for column in tree["columns"]:
            arrow = ""
            if sort_state["column"] == column:
                arrow = " ▼" if sort_state["reverse"] else " ▲"
            tree.heading(
                column, text=f"{FIELD_LABELS[column]}{arrow}",
                command=lambda selected=column: sort_by_column(selected)
            )

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)
        columns = selected_columns()
        tree.configure(columns=columns)
        widths = {
            "first_name": 110, "last_name": 110, "age": 55, "address": 220,
            "birthdate": 95, "mobile_number": 120, "email": 210, "gender": 90,
            "username": 130, "company": 150, "job_title": 150, "country": 110
        }
        for column in columns:
            tree.column(column, width=widths[column], minwidth=55, anchor="w")
        update_headings()
        records = load_records(columns)
        for rec in records:
            tree.insert("", "end", values=rec[1:])
        if sort_state["column"] in columns:
            sort_rows(sort_state["column"], sort_state["reverse"])
        status.config(
            text=f"Total records in database: {len(records)}"
            if columns else "Select at least one column to preview records."
        )

    def handle_generate():
        try:
            count = int(count_var.get())
            if not (MIN_RECORDS <= count <= MAX_RECORDS):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", f"Enter a number between {MIN_RECORDS} and {MAX_RECORDS}.")
            return

        columns = selected_columns()
        if not columns:
            messagebox.showwarning("No Columns Selected", "Select at least one field to generate.")
            return
        recs = [generate_record(columns) for _ in range(count)]
        save_records(recs, columns)
        refresh_table()
        messagebox.showinfo("Success", f"Generated and stored {count} fake records!")

    def handle_clear():
        if messagebox.askyesno("Confirm", "Delete all stored fake records?"):
            delete_all_records()
            refresh_table()

    def handle_export():
        columns = selected_columns()
        if not columns:
            messagebox.showwarning("No Columns Selected", "Select at least one field to export.")
            return
        records = load_records(columns)
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
                writer.writerow([FIELD_LABELS[column] for column in columns])
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

    tree = ttk.Treeview(table_frame, style="FDG.Treeview", columns=(), show="headings", height=11)

    y_scroll = ttk.Scrollbar(
        table_frame, orient="vertical", style="Vertical.TScrollbar",
        command=tree.yview
    )
    x_scroll = ttk.Scrollbar(
        table_frame, orient="horizontal", style="Horizontal.TScrollbar",
        command=tree.xview
    )
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