# MD Viewer — Phased Implementation Prompts

Build the application one phase at a time. After each phase, run the
listed commands and confirm the verification step passes before starting
the next phase.

---

## Phase 1 — Django Skeleton

> Copy and send this prompt to the AI:

---

Read `spec.md`. Implement **Phase 1 only** — all sections tagged
`<!-- phase:1 -->`: "Python Environment Setup", "App Creation Overview",
"Django Project Configuration", and "YAML Configuration File".

The Django project does not exist yet. Create these files from scratch:

- `requirements.txt`
- `mdviewer.yaml` — use the example values from the "YAML Configuration
  File" section of the spec
- `manage.py`
- `mdviewer/__init__.py`
- `mdviewer/settings.py`
- `mdviewer/wsgi.py`
- `mdviewer/asgi.py`
- `mdviewer/urls.py`
- `library/__init__.py`
- `library/apps.py`
- `library/middleware.py` — CSP middleware class only
- `library/api_urls.py` — **stub only**: `urlpatterns = []` with no
  imports from `library.views`. The real content is added in Phase 3.
- `library/urls.py` — full content (uses only Django's `TemplateView`,
  no imports from `library.views`)

Also create these empty directories (add a `.gitkeep` file in each):

- `db/`
- `logs/`
- `templates/library/`
- `library/static/library/css/`

**Do not implement:** `library/models.py`, `library/serializers.py`,
`library/views.py`, `library/throttles.py`, or any HTML templates.
Do not add per-endpoint throttle scope rates to `settings.py` — those
are added in Phase 3.

When done, list every file you created.

---

**After the AI is done, you run** (in order):

```bash
pip install -r requirements.txt

# Generate a random secret key and set it for the current shell session.
# Windows cmd: set DJANGO_SECRET_KEY=<paste a long random string>
# Windows PowerShell: $env:DJANGO_SECRET_KEY="<paste a long random string>"
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"

python manage.py check
```

**Phase 1 is complete when:** `python manage.py check` exits with
`System check identified no issues (0 silenced).`

---

## Phase 2 — Database Model

> Copy and send this prompt to the AI:

---

Read `spec.md` and `db-spec.md`. Implement **Phase 2 only** — the
section tagged `<!-- phase:2 -->` in `spec.md`: "Database Layer".

Use `db-spec.md` as a cross-reference: the DDL there is the exact SQL
schema the Django model must produce. Verify that every column name,
type, default value, CHECK constraint, UNIQUE constraint, and index in
the DDL has a corresponding field or `Meta` entry in the model. Note
in particular:

- `db_table = 'mdlibrary'` (overrides Django's default `library_mdlibrary`)
- The `UNIQUE` constraint on `(file_name, file_version)` and the index
  on `file_name` are both declared in `Meta`
- `deleted` is a `BooleanField` — Django maps it to SQLite `INTEGER`
  `0`/`1` transparently
- `created_at` uses `auto_now_add=True`; `updated_at` uses `auto_now=True`

The Phase 1 files already exist. Create only:

- `library/models.py` — the `MdLibrary` model with all fields,
  constraints, indexes, and `Meta` class exactly as specified.

Do not modify any existing file. Do not create serializers, views,
throttles, or templates.

When done, show the file you created.

---

**After the AI is done, you run:**

```bash
python manage.py makemigrations library
python manage.py migrate
```

**Phase 2 is complete when:** both commands exit without errors and the
following prints `OK`:

```bash
python manage.py shell -c "from library.models import MdLibrary; print('OK')"
```

---

## Phase 3 — REST API Layer

> Copy and send this prompt to the AI:

---

Read `spec.md`. Implement **Phase 3 only** — all sections tagged
`<!-- phase:3 -->`: "ORM/API Layer" (all subsections: Security
Considerations, URL Structure, Serializer Design, HTTP Status Codes,
JSON Response Schema, and all Endpoint Specifications). Also read
`### URL Configuration <!-- phase:1, phase:3 -->` for `library/api_urls.py`.

The Phase 1 and Phase 2 files already exist. Create or modify:

**Create:**

- `library/serializers.py`
- `library/throttles.py`
- `library/views.py`

**Replace** (currently a stub with empty `urlpatterns`):

- `library/api_urls.py` — replace the stub with the full routing from
  the spec. Remember: `stats/` must be declared before `<int:pk>/`.

**Modify** (add throttle scopes to the existing dict):

- `mdviewer/settings.py` — add all per-endpoint throttle scope keys and
  rates to `DEFAULT_THROTTLE_RATES` in `REST_FRAMEWORK`, per the Rate
  Limiting table in the spec.

Do not create or modify any HTML templates or static CSS files.

When done, list every file you created or modified.

---

**After the AI is done, you run:**

```bash
python manage.py check
python manage.py runserver
```

Then in a separate terminal, test the API:

```bash
# Should return {"status": "SUCCESS", "count": 0, "results": []}
curl -s http://localhost:8000/api/v1/library/ | python -m json.tool

# Should return {"status": "SUCCESS", "active_files": 0, ...}
curl -s http://localhost:8000/api/v1/library/stats/ | python -m json.tool
```

**Phase 3 is complete when:** both curl calls return valid JSON with
`"status": "SUCCESS"`.

---

## Phase 4 — Frontend and Templates

> Copy and send this prompt to the AI:

---

Read `spec.md`. Implement **Phase 4 only** — the section tagged
`<!-- phase:4 -->`: "Web Frontend" (all subsections: Web Frontend
Security, Web UI Color Scheme, Frontend Web Libraries, Common Header
and Fonts, Navigation Bar, Search Page, Upload Page, Admin Page).

The Phase 1–3 files already exist. Create only these files — do not
modify any Python files:

- `templates/base.html` — base template with `{% load static %}`, all
  CDN links in the specified load order, Pygments CSS link, common
  header with Workbench font and dark/light mode toggle, Bootstrap
  navbar, and `$.ajaxSetup()` CSRF configuration
- `templates/library/search.html` — extends base; full search form,
  results table, and tab area with per-tab Rendered/Raw toggle
- `templates/library/upload.html` — extends base; upload form card with
  FileReader auto-populate
- `templates/library/admin.html` — extends base; stats cards, filter
  toggle buttons, records table, and delete confirmation modal
- `library/static/library/css/pygments.css` — write a single comment
  line as a placeholder:
  `/* Regenerate: python -c "from pygments.formatters import HtmlFormatter; print(HtmlFormatter(style='default').get_style_defs('.highlight'))" > library/static/library/css/pygments.css */`

When done, list every file you created.

---

**After the AI is done, you run:**

Generate the real Pygments CSS (overwrites the placeholder):

```bash
python -c "from pygments.formatters import HtmlFormatter; print(HtmlFormatter(style='default').get_style_defs('.highlight'))" > library/static/library/css/pygments.css
```

Collect static files and start the server:

```bash
python manage.py collectstatic --noinput
python manage.py runserver
```

**Phase 4 is complete when:** all three pages load in a browser at
`http://localhost:8000` without JavaScript console errors.
