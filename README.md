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
- `SMS_and_Email.py` provides single-recipient SMS and email simulation, with
  delivery history stored in SQLite.
- `sms_provider.py` sends SMS through the Twilio REST API using Python's
  standard library.
- `email_provider.py` sends email through Gmail's SSL-protected SMTP service.
- `FakeDataGeneration.py` generates records, stores them in SQLite, and offers
  field selection, sortable previews, and CSV export.
- `URL_Shortening.py` provides the URL-shortening utility.

## Features

- Sign up with a unique username and email, and log in using either.
- Passwords are never stored as plain text. Each account gets a random 16-byte
  salt and a PBKDF2-HMAC-SHA256 password hash (200,000 iterations).
- The SMS/email view has a scrollable layout, channel-aware personal-contact
  quick fill, delivery notifications, a live log, and a persistent history
  table. Single-number SMS uses Twilio when configured; email uses Gmail SMTP
  when configured. Both channels clearly show LIVE or SIMULATED mode.
- Fake data fields can be selected independently. Batch generation, table
  preview, sorting, and CSV export use the selected fields.
- URL shortening uses the TinyURL service and requires an internet connection.
  If the service is unavailable, the app reports the failure instead of
  presenting a nonfunctional link.
- The database and all generated data are stored locally in `project.db`.

## Run the application

Python 3.8 or newer is recommended. Twilio support uses Python's standard
library; `winotify` enables Windows desktop notifications. Install the project
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

## Configure Twilio SMS

In the **SMS & Email** tab, open **SMS Settings** and enter your Twilio Account
SID, Auth Token, and Twilio phone number. Settings entered in the dialog are
kept in memory only for the current run. Alternatively, set these environment
variables before starting the application to prefill the settings:

```powershell
$env:TWILIO_ACCOUNT_SID = "your-account-sid"
$env:TWILIO_AUTH_TOKEN = "your-auth-token"
$env:TWILIO_PHONE_NUMBER = "+15551234567"
python Main.py
```

The SMS tab displays **LIVE** only when all three settings are present;
otherwise SMS sends are simulated and no API request is made. A live single-
recipient send creates a message with `POST /Messages.json`, then checks its
current delivery status with `GET /Messages/{sid}.json`. A successful API
request does not guarantee delivery. Twilio trial accounts can only send to
phone numbers verified in the Twilio console. The app does not route bulk sends
through Twilio.

## Configure Gmail SMTP email

For Gmail, enable 2-Step Verification and create an App Password in your Google
Account security settings. Use the App Password, not your regular Google
password. Set the following variables in the same PowerShell session used to
start the app:

```powershell
$env:SENDER_GMAIL = "your-address@gmail.com"
$env:GMAIL_APP_PASSWORD = "your16charapppassword"
python Main.py
```

Email uses `smtp.gmail.com` over SSL on port 465. The Email badge displays
**LIVE** when both variables are present; otherwise sending is simulated and no
email is sent. Credentials are not saved to the database or source code.

Run the automated tests with:

```powershell
python -m unittest discover -s tests -v
```

Twilio tests use a local fake server, and email and URL-shortening tests mock
their services, so the suite does not send real messages or create short links.
Install `winotify` with
`python -m pip install winotify` to
enable Windows system toasts; in-app notifications remain available if the
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
