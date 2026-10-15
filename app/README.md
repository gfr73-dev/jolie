# Printer Installation Requests - Flask replacement for IBM Notes

This project is a copy-paste-ready Flask application for the `JOLIE` MySQL database.
It replaces the IBM Notes form `Account com ODBC AS400` and manages printer installation requests.

## Main features

- Login using `register_users`.
- Landing page lists all requests and filters by status.
- Account lookup validates exactly 8 numeric characters before any AS400 call.
- Existing account is checked before lookup and before save, preventing MySQL unique-index errors.
- Lookup fields are stored in `register_request` and rendered read-only.
- Installation type drives initial request status and printer validation requirement.
- Admin-only request status changes using `install_status`.
- Separate view for `Aguarda Validação Impressora`.
- Printer validation can only be changed by admins or users with `is_dir_reg=true`.
- Email notifications for validation and IT installation workflow.

## Install

1. Create the database and tables:

```bash
mysql -u root -p < scripts/schema.sql
```

2. Install dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

3. Configure environment:

```bash
cp .env.example .env
```

Edit `.env` with your MySQL, SMTP and AS400 details.

4. Seed base data:

```bash
python scripts/seed.py
```

5. Run:

```bash
flask run
```

Default seeded admin:

- username: `admin@example.com`
- password: `admin123!`

Change it immediately after first login.

## Notes

- The table list from the request says `install_status`, while the business rule mentions `request_status`. This project uses `install_status` consistently.
- No new database table was added for account managers. The dropdown is driven by `ACCOUNT_MANAGERS` in `.env` to respect your requested database structure.
- If `AS400_ENABLED=false`, lookup returns mock data so the UI can be tested without ODBC.
