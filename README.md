# Python Tkinter Utilities Application Suite

A desktop utilities suite built with Python's standard-library Tkinter GUI and
SQLite. It includes account login, URL shortening, an SMS/email utility, and a
customizable fake-data generator.

## Architecture

- `Main.py` starts the application, initializes the account database, and builds
  the tabbed utilities interface.
- `Login.py` contains the login and sign-up screens.
- `auth.py` stores accounts and validates credentials using PBKDF2-HMAC-SHA256.
- `Database.py` defines the local SQLite database file as `project.db`.
- `SMS_and_Email.py` sends email through Gmail SMTP when configured, posts SMS
  test requests to HTTPBin, and stores delivery history in SQLite.
- `FakeDataGeneration.py` generates records, stores them in SQLite, and offers
  field selection, sortable previews, and CSV export.
- `URL_Shortening.py` provides the URL-shortening utility.

## Features

- Sign up with a unique username and email, and log in using either.
- Passwords are never stored as plain text. Each account gets a random 16-byte
  salt and a PBKDF2-HMAC-SHA256 password hash (200,000 iterations).
- The SMS/email view has a scrollable layout, channel-aware personal-contact
  quick fill, delivery notifications, a live log, and a persistent history
  table. Email uses Gmail SMTP when configured; without credentials it records
  a clearly labeled local simulation. SMS requests are posted to HTTPBin for
  testing and do not send a real SMS.
- Fake data fields can be selected independently. Batch generation, table
  preview, sorting, and CSV export use the selected fields.
- The database and all generated data are stored locally in `project.db`.

## Run the application

Python 3.8 or newer is recommended. The application uses standard-library
modules plus `winotify` for Windows desktop notifications. Install the project
dependency with:

```powershell
python -m pip install -r requirements.txt
```

From the project directory, run:

```powershell
python Main.py
```

The application creates `project.db` in the current working directory when
needed. Use **Sign Up** to create the first account.

## Configure Gmail delivery

Real email delivery requires a Gmail address and a 16-character Google App
Password. Enable 2-Step Verification and create an App Password in your Google
Account security settings. Set the following environment variables in the
PowerShell session before starting the application; do not put credentials in
source code or commit them:

```powershell
$env:SENDER_GMAIL = "your-address@gmail.com"
$env:GMAIL_APP_PASSWORD = "your16charapppassword"
python Main.py
```

If these values are missing, email dispatch is recorded as a simulated SMTP
delivery and the live log explains how to configure Gmail. The SMS test sends
the phone number and message body to `https://httpbin.org/post`; HTTPBin is a
public request-testing service, not an SMS carrier. Use non-sensitive test
content for that mode. Install `winotify` with `python -m pip install winotify`
to enable Windows system toasts; in-app notifications remain available if the
package is unavailable.

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
