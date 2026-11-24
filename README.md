# Python Tkinter Utilities Application Suite

A desktop utilities suite built with Python's standard-library Tkinter GUI and
SQLite. It includes account login, URL shortening, an offline SMS/email
dispatcher, and a customizable fake-data generator.

## Architecture

- `Main.py` starts the application, initializes the account database, and builds
  the tabbed utilities interface.
- `Login.py` contains the login and sign-up screens.
- `auth.py` stores accounts and validates credentials using PBKDF2-HMAC-SHA256.
- `Database.py` defines the local SQLite database file as `project.db`.
- `SMS_and_Email.py` simulates message delivery and stores a persistent
  dispatch history in SQLite. It does not connect to external messaging
  services.
- `FakeDataGeneration.py` generates records, stores them in SQLite, and offers
  field selection, sortable previews, and CSV export.
- `URL_Shortening.py` provides the URL-shortening utility.

## Features

- Sign up with a unique username and email, and log in using either.
- Passwords are never stored as plain text. Each account gets a random 16-byte
  salt and a PBKDF2-HMAC-SHA256 password hash (200,000 iterations).
- Simulated SMS and email dispatch includes configurable personal email/number
  quick-fill fields, a live log, and a persistent dispatched-messages table.
- Fake data fields can be selected independently. Batch generation, table
  preview, sorting, and CSV export use the selected fields.
- The database and all generated data are stored locally in `project.db`.

## Run the application

Python 3.8 or newer is recommended. The application uses only Python
standard-library modules.

From the project directory, run:

```powershell
python Main.py
```

The application creates `project.db` in the current working directory when
needed. Use **Sign Up** to create the first account.

## Inspect password hashing in `project.db`

The `users` table stores `username`, `email`, `salt`, and `password_hash`.
SQLite stores the salt and hash as binary values (BLOBs); convert them to
hexadecimal to inspect their contents:

```sql
SELECT username, email, hex(salt) AS salt_hex,
       hex(password_hash) AS password_hash_hex
FROM users;
```

You can run that query with a SQLite viewer, or from Python:

```powershell
python -c "import sqlite3; c=sqlite3.connect('project.db'); print(c.execute('SELECT username,email,hex(salt),hex(password_hash) FROM users').fetchall()); c.close()"
```

Each account has a distinct random salt, so identical passwords do not produce
identical stored hashes. Hashing and login verification are implemented in
`auth.py`.
