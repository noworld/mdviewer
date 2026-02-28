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
```

Generate and permanently save a secret key as a user-level environment
variable (persists across terminal sessions — do this once):

```
# Windows cmd (run once — survives terminal restarts):
python -c "import secrets; print(secrets.token_urlsafe(50))"
# Copy the output, then:
setx DJANGO_SECRET_KEY "<paste output here>"
# Close and reopen your terminal for setx to take effect.

# macOS / Linux (add to your shell profile, e.g. ~/.bashrc or ~/.zshrc):
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
```

Then verify the project is configured correctly:

```bash
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

## Phase 4 — Base Template and Upload Page

> Copy and send this prompt to the AI:

---

Read `spec.md`. Implement **Phase 4 only** — the subsections of
`## Web Frontend <!-- phase:4, phase:5 -->` tagged `<!-- phase:4 -->`:
"Web Frontend Security", "Web UI Color Scheme", "Frontend Web
Libraries", "Common Header and Fonts", "Navigation Bar", "List of
Pages", and "Upload Page".

The Phase 1–3 files already exist. Create only these files — do not
modify any Python files:

- `templates/base.html` — base template with `{% load static %}`, all
  CDN links in the specified load order, Pygments CSS link, common
  header with Workbench font and dark/light mode toggle, Bootstrap
  navbar, and `$.ajaxSetup()` CSRF configuration
- `templates/library/upload.html` — extends base; upload form card with
  FileReader auto-populate, client-side validation, and AJAX feedback
  alerts
- `library/static/library/css/pygments.css` — write a single comment
  line as a placeholder:
  `/* Regenerate: python -c "from pygments.formatters import HtmlFormatter; print(HtmlFormatter(style='default').get_style_defs('.highlight'))" > library/static/library/css/pygments.css */`

**Do not implement:** `templates/library/search.html` or
`templates/library/admin.html` — those are Phase 5.

When done, list every file you created.

---

**After the AI is done, you run:**

Generate the real Pygments CSS (overwrites the placeholder):

```bash
python -c "from pygments.formatters import HtmlFormatter; print(HtmlFormatter(style='default').get_style_defs('.highlight'))" > library/static/library/css/pygments.css
```

Start the server:

```bash
python manage.py runserver
```

**Phase 4 is complete when:** `http://localhost:8000/upload/` loads in a
browser with correct Bootstrap styling, the light/dark mode toggle works
and persists across page loads, and the browser JavaScript console shows
no errors.

---

## Phase 5 — Search and Admin Pages

> Copy and send this prompt to the AI:

---

Read `spec.md`. Implement **Phase 5 only** — the subsections of
`## Web Frontend <!-- phase:4, phase:5 -->` tagged `<!-- phase:5 -->`:
"Search Page" and "Admin Page".

The Phase 1–4 files already exist, including `templates/base.html`.
Extend it. Create only these files — do not modify any existing file:

- `templates/library/search.html` — extends base; search form, results
  table using Bootstrap-Table, and the tab area with per-tab
  Rendered/Raw toggle. Key behaviours to implement exactly:
  - View button reads `data-id` from its row to call
    `GET /api/v1/library/{id}/`
  - Opening a file already open switches focus to its existing tab
    rather than duplicating it
  - Each tab independently tracks its own Rendered/Raw toggle state
  - Tab content is cached in the DOM — no re-fetch when switching tabs
  - Tab area is hidden on page load; shown when first tab opens; hidden
    again when last tab is closed
- `templates/library/admin.html` — extends base; stats cards loaded via
  `GET /api/v1/library/stats/` on page load, filter toggle buttons
  (Active Only pre-selected), Bootstrap-Table records table,
  client-side file name filter input, delete confirmation modal, and
  inline row updates (badge + button swap without full table reload)

When done, list every file you created.

---

**After the AI is done, you run:**

Collect static files and start the server:

```bash
python manage.py collectstatic --noinput
python manage.py runserver
```

**Phase 5 is complete when:** all three pages load at
`http://localhost:8000` without JavaScript console errors, the search
tab system opens and closes files correctly, and the admin delete and
undelete actions update the row in place.
