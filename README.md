# mdviewer

A lightweight desktop web application for managing a collection of Markdown documents. Upload `.md` files into a SQLite database, then browse, search, and view them as rendered HTML or raw text. There is no authentication — it is designed for single-user, local-machine use only.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Django 5.1 |
| REST API | Django REST Framework 3.15 |
| Markdown rendering | python-markdown 3.7 + Pygments 2.18 |
| HTML sanitization | nh3 0.2 |
| Configuration | PyYAML 6.0 |
| Database | SQLite |
| Frontend | Bootstrap 5, Bootstrap-Table, Bootstrap-Icons, jQuery, Google Fonts (all via CDN) |

---

## Developer Quickstart

### Prerequisites

- Python 3.12+
- PowerShell (Windows) or bash (macOS/Linux)

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd mdviewer
python -m venv venv
```

### 2. Activate the virtual environment

```powershell
# PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set the Django secret key (required — do this once)

Django requires a `SECRET_KEY` for cryptographic operations (CSRF tokens, signed cookies, etc.). This project deliberately **never** stores the key in a file that could end up in version control. Instead it reads the key exclusively from the `DJANGO_SECRET_KEY` environment variable, and will refuse to start if the variable is not set.

**Generate a key:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Set it persistently (survives terminal restarts):**

```powershell
# Windows — run once in any terminal; takes effect after you open a new terminal
setx DJANGO_SECRET_KEY "<paste generated key here>"
```

```bash
# macOS / Linux — add this line to ~/.bashrc or ~/.zshrc, then restart your shell
export DJANGO_SECRET_KEY="<paste generated key here>"
```

> **`django-secret-key.ps1`** is a convenience script that sets the variable for the **current PowerShell session only** (`$env:DJANGO_SECRET_KEY = "..."`). It does not persist across terminal restarts. Use `setx` (Windows) or your shell profile (macOS/Linux) for a durable setting. If you regenerate a key, update `django-secret-key.ps1` with the new value so the session script stays in sync.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Generate the Pygments syntax-highlighting CSS

```bash
python -c "from pygments.formatters import HtmlFormatter; print(HtmlFormatter(style='default').get_style_defs('.highlight'))" > library/static/library/css/pygments.css
```

### 7. Collect static files

```bash
python manage.py collectstatic --noinput
# or just run:
.\collectstatic.ps1
```

See the [collectstatic section](#about-collectstaticps1) below for why this is needed.

### 8. Run the development server

```bash
python manage.py runserver
```

Open `http://localhost:8000` in your browser.

---

## Configuration

All runtime configuration lives in `mdviewer.yaml` at the project root:

```yaml
database_path: db/mdviewer.db   # path to SQLite file, relative to project root
log_directory: logs             # directory for mdviewer.log
log_level: INFO                 # DEBUG, INFO, WARNING, ERROR
debug: true                     # must be true when using runserver (see gotchas)
allowed_hosts:
  - localhost
  - 127.0.0.1
max_upload_bytes: 1048576       # 1 MB upload limit
```

---

## About `collectstatic.ps1`

Django's `collectstatic` command gathers every static file (CSS, JS, images) from each app's `static/` directory and copies them all into a single `staticfiles/` directory at the project root (`STATIC_ROOT`). This is the directory a production web server (nginx, IIS, etc.) would serve directly.

In development with `DEBUG = true`, Django's `runserver` serves static files directly from each app's `static/` directory, so `collectstatic` is not strictly required for day-to-day development. However, it **is** required after generating `pygments.css` for the first time, or any time you add or modify a static file, if you want those changes visible in a production-style setup.

`collectstatic.ps1` is a one-liner wrapper:

```powershell
python manage.py collectstatic --noinput
```

Run it whenever you regenerate `pygments.css` or pull changes that include new static assets.

---

## Pages

| URL | Page |
|---|---|
| `/` | Redirects to `/search/` |
| `/upload/` | Upload a Markdown file |
| `/search/` | Browse, search, and view documents |
| `/admin/` | Stats dashboard, delete/undelete records |

---

## REST API

Base path: `/api/v1/`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `library/` | List all non-deleted documents |
| `POST` | `library/` | Upload a new document |
| `GET` | `library/stats/` | Aggregate statistics |
| `GET` | `library/<id>/` | Retrieve a document with rendered HTML |
| `PATCH` | `library/<id>/` | Update soft-delete flag |
| `DELETE` | `library/<id>/` | Hard-delete a document |

---

## Gotchas

**`DJANGO_SECRET_KEY` must be set before anything works.**
`settings.py` raises `RuntimeError` immediately on startup if the variable is absent. If you see that error, set the variable as described above.

**`debug: true` is required when using `runserver`.**
When `DEBUG = false`, Django's development server stops serving static files. The app will load but all CSS and JS will be missing. Only set `debug: false` if you are running behind a real web server that serves `STATIC_ROOT` directly.

**Every inline `<script>` tag must carry a CSP nonce.**
A custom Content Security Policy middleware generates a unique nonce for every request and attaches it to `request.csp_nonce`. Any inline `<script>` tag in a template that omits `nonce="{{ request.csp_nonce }}"` will be silently blocked by the browser. CDN `<script src="...">` tags do not need a nonce.

**Regenerate `pygments.css` after any Pygments upgrade.**
The CSS is generated from the installed Pygments library at a point in time. If you upgrade Pygments, re-run the generation command in step 6 and then run `collectstatic`.

**`django-secret-key.ps1` is session-scoped.**
Running the script sets the key only for that PowerShell window. A new terminal will not have it. Use `setx` for a persistent setting.

**The `logs/` and `db/` directories must exist.**
They are included in the repo via `.gitkeep` files, so a fresh clone will have them. If they are accidentally deleted, re-create them before starting the server, or Django will fail trying to open the log file and database.

---

## Generating the App with AI (Phased Prompts)

`phased_prompts.md` contains five copy-paste prompts — one per implementation phase — for regenerating the entire application from scratch using an AI coding assistant. Each prompt targets a specific tagged section of `spec.md`:

| Phase | What it builds | Verification |
|---|---|---|
| 1 | Django project skeleton, settings, YAML config, CSP middleware | `python manage.py check` |
| 2 | `MdLibrary` database model and migration | `python manage.py shell -c "from library.models import MdLibrary; print('OK')"` |
| 3 | REST API — serializers, views, throttles, URL routes | `curl http://localhost:8000/api/v1/library/` returns JSON |
| 4 | Base template, upload page, Pygments CSS placeholder | Upload page loads with correct styling |
| 5 | Search page (tab viewer) and admin page | All three pages load without JS console errors |

**Workflow:** copy the prompt for the current phase from `phased_prompts.md`, paste it into your AI assistant, let it generate the files, then run the listed verification commands before moving to the next phase. The prompts are designed to be self-contained — each one references the spec sections it needs and explicitly lists which files to create or modify.
