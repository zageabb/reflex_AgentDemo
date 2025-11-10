# Reflex Agent Demo

The Reflex Agent Demo is a lightweight Flask application that showcases how scripted product scenarios, supporting UI snippets, and narrated agent flows come together for stakeholder demos. The project borrows the upbeat, practical tone used in the [`zageabb/Flask_Question`](https://github.com/zageabb/Flask_Question) README—expect concise direction, inline tips, and callouts for anything you need to prep before presenting.

## Environment Setup

1. **Pick a Python (3.10+) runtime.** The sample project was authored against Python 3.12, but any modern 3.10+ interpreter works fine.
2. **Create your virtual environment.**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. **Install dependencies from `requirements.txt`.**
   ```bash
   pip install -r requirements.txt
   ```
4. **Copy `.env.example` → `.env` and personalize it.**
   ```bash
   cp .env.example .env
   ```
   Update secrets before you ship anything external.

## Configuration via `.env`

`python-dotenv` loads environment variables before the app boots. The keys you will usually set are:

| Variable | Purpose | Notes |
| --- | --- | --- |
| `FLASK_ENV` | Chooses the configuration block in `config.py`. | `development` enables debug mode and live reload. |
| `SECRET_KEY` | Signs session cookies and CSRF tokens. | Generate a unique value (`python -c "import secrets; print(secrets.token_hex())"`). |
| `ADMIN_USER` / `ADMIN_PASSWORD` | Seeds an admin account on first run. | Only applied if both values exist and the username is new. |
| `DATABASE_URL` | Override the default SQLite path. | Falls back to `instance/app.db` when unset. |
| `MAX_CONTENT_LENGTH` | Restricts upload size (bytes). | Defaults to `16 * 1024 * 1024`. |
| `UPLOAD_EXTENSIONS` | Comma-separated whitelist of upload file extensions. | Default accepts `.txt,.md,.json,.pdf`. |

Remember to restart the dev server after tweaking `.env` files. Flask caches configuration at startup.

## Running the App with `flask run`

1. Ensure the virtual environment is active and `.env` exists.
2. Set the Flask entry point to `app.py`:
   ```bash
   export FLASK_APP=app.py  # Windows PowerShell: $env:FLASK_APP = "app.py"
   ```
3. (Optional) Enable the debugger:
   ```bash
   export FLASK_DEBUG=1
   ```
4. Start the development server:
   ```bash
   flask run
   ```
   The included `.flaskenv` pins the dev server to port `5010`, so you don't need to add `--port` manually.
5. Visit `http://127.0.0.1:5010/` in your browser. The admin dashboard lives under `/admin`.

`flask run` respects the `.env` file; your secrets and database URL are injected automatically. For production you should run the app through `gunicorn` or another WSGI server and set environment variables outside of `.env`.

## Admin Credentials & Workflow Tips

- **Seeded admin:** The `ADMIN_USER` / `ADMIN_PASSWORD` pair in `.env` create an administrator on the first boot. Use throwaway values in dev, rotate them in staging.
- **Manual creation:** Need to change the admin later? Run `python create_admin.py <username> <password> [--email someone@company.com]`. Add `--update` to reset an existing password.
- **Dashboard orientation:** Once logged in, `/admin` lets you upload new HTML/Markdown snippets, stage JSON scenarios, and reorder demo flows without touching the repository.
- **Instance storage:** Uploaded files land in `instance/uploads/` (gitignored). Clean the folder before committing.

## Repository Layout Highlights

| Folder | Behavior |
| --- | --- |
| `app/` | Flask application package (blueprints, forms, templates, models). |
| `data/scenarios/` | JSON conversation scripts that the demo player consumes. IDs should match filenames. |
| `data/snippets/` | HTML, Markdown, or plain-text fragments referenced by scenarios. Nested folders mirror categories. |
| `instance/` | Runtime-only assets (SQLite database, uploaded files). Not checked into git. |
| `docs/` | Product and UX documentation—including the design brief and optional UI mock asset. |

## Developer Notes

- Use the `create_admin.py` helper when sharing a database across teammates—no one needs to hand-edit hashed passwords.
- Keep snippet filenames descriptive; the player displays them in the sidebar when troubleshooting a flow.
- Treat `data/` as read-only in production deployments. Author edits in source control, then sync to the server.

Additional design context lives in [`docs/design.md`](docs/design.md).
