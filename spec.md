# MD Viewer App

MdViewer - Markdown database and viewer

---

## Summary 

This app will maintain a database (Sqlite) that stores markdown files and a web app that allows the user to select, view, and delete markdown files. No markdown editing will be required; only uploading markdown and then viewing the markdown. The markdown can be viewed both as rendered HTML and the raw markdown file. This is a simple app that will run on a desktop using Python version 3.12.2, so SQLite will be sufficient for a database and no login will be required.

## Tech Stack

This web app is based on Python. Django will be used for the web front end, API calls, and an ORM layer, and SQLite will be used for the database. The front end can use javascript libraries and fonts via CDN. Configuration files will be in YAML format.

### Tech Stack Summary

* Python 3
* Django for the web application
* Python-markdown for handling markdown rendering
* nh3 for preventing XSS or reflection attacks from getting into generated HTML
* Pygments for code blocks
* DjangoRestFramework for the ORM/API layer
* PYYaml for yaml configuration files
* jQuery for dynamic HTML and Javascript
* Bootstrap for web formatting
* Bootstrap-Table for HTML/Javascript data table display
* Bootstrap-Icons for web icons
* Google Fonts for web fonts
* SQLite for the database

Neither django-markdown-deux nor any Django-specific HTML sanitization integration is required. Use nh3 directly in the view/API layer to sanitize rendered HTML output from python-markdown.

## Python Environment Setup
* Ensure that Python is updated to the most current version of Python 3
* Ensure that Python PIP is updated to the most current version
* Create a python virtual environment
* Ensure that Python PIP in the virtual environment is updated to the most current version
* Install the required Python packages into the virtual environment: `pip install -r requirements.txt`

The `requirements.txt` file must include the following packages:

```
Django~=5.1
djangorestframework~=3.15
Markdown~=3.7
nh3~=0.2
Pygments~=2.18
PyYAML~=6.0
```

## App Creation Overview
* Create the Django project
* Make sure to run manage.py migrate after changing your settings.
* Be sure to regenerate static when done making changes.
* Create the SQLite Database according to the 'Database Layer' parameters below.
* Create the YAML configuation file according to the 'YAML Configuration File' parameters below.
* Create the Django ORM layer models according to the 'Database Layer' and 'ORM/API Layer' parameters below.
* Create the REST API according to the 'ORM/API Layer' parameters below.
* Create the Django web app according to the 'Web Frontend' parameters below.

## Django Project Configuration

### Project and App Names

| | Name | Create Command |
|---|---|---|
| Django project | `mdviewer` | `django-admin startproject mdviewer .` (trailing dot — avoids a nested `mdviewer/mdviewer/` directory) |
| Django app | `library` | `python manage.py startapp library` |

### settings.py Configuration

Configure `mdviewer/settings.py` as follows.

#### INSTALLED_APPS

Include only what is needed. Remove the default `admin`, `auth`, `contenttypes`, `sessions`, and `messages` apps — no login or admin interface is required.

```python
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'rest_framework',
    'library',
]
```

#### MIDDLEWARE

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'library.middleware.ContentSecurityPolicyMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

#### REST_FRAMEWORK

Per-endpoint rate limits are applied using custom per-view throttle classes (one class per endpoint). The `DEFAULT_THROTTLE_RATES` entry below is a global fallback; each view's throttle class defines its own rate per the Rate Limiting table in the ORM/API Security section.

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
```

#### DATABASES

Read the SQLite file path from the YAML configuration file loaded at startup (see YAML Configuration File section):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / YAML_CONFIG['database_path'],
    }
}
```

#### TEMPLATES

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]
```

#### STATIC FILES

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### SECURITY AND REQUEST SETTINGS

```python
DEBUG = YAML_CONFIG['debug']
try:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # Never hard-code or store in YAML
except KeyError:
    raise RuntimeError("Set the DJANGO_SECRET_KEY environment variable before starting the application.")
ALLOWED_HOSTS = YAML_CONFIG['allowed_hosts']

SECURE_CONTENT_TYPE_NOSNIFF = True                         # sets X-Content-Type-Options: nosniff
X_FRAME_OPTIONS = 'DENY'                                   # sets X-Frame-Options: DENY
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin' # sets Referrer-Policy header

# Reject oversized request bodies before they reach the view layer.
# Add headroom above max_upload_bytes to account for request envelope overhead.
DATA_UPLOAD_MAX_MEMORY_SIZE = YAML_CONFIG['max_upload_bytes'] + 100_000
```

#### LOGGING

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / YAML_CONFIG['log_directory'] / 'mdviewer.log'),
            'formatter': 'standard',
        },
    },
    'loggers': {
        'library': {
            'handlers': ['file'],
            'level': YAML_CONFIG['log_level'],
            'propagate': False,
        },
    },
}
```

#### CSP Middleware

Django's `SecurityMiddleware` does not set a `Content-Security-Policy` header. Implement it as a custom middleware class in `library/middleware.py`:

```python
class ContentSecurityPolicyMiddleware:
    CSP_VALUE = (
        "default-src 'self'; "
        "script-src 'self' ajax.googleapis.com; "
        "style-src 'self' ajax.googleapis.com cdn.jsdelivr.net fonts.googleapis.com; "
        "font-src fonts.gstatic.com cdn.jsdelivr.net; "
        "img-src 'self' https: data:; "
        "frame-ancestors 'none'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self.CSP_VALUE
        return response
```

This middleware must be listed in `MIDDLEWARE` immediately after `SecurityMiddleware` (see MIDDLEWARE section above).

### URL Configuration

Create the following URL configuration files.

**`mdviewer/urls.py`** — root URL conf:

```python
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('library.api_urls')),
    path('', include('library.urls')),
]
```

**`library/api_urls.py`** — API routes. The `stats/` path **must be declared before `<int:pk>/`** to prevent the literal string "stats" from being matched as an integer primary key:

```python
from django.urls import path
from library import views

urlpatterns = [
    path('library/', views.LibraryListCreateView.as_view()),
    path('library/stats/', views.LibraryStatsView.as_view()),
    path('library/<int:pk>/', views.LibraryDetailView.as_view()),
]
```

**`library/urls.py`** — page view routes. All page views are served as `TemplateView` instances with no extra context — all data is loaded client-side via AJAX:

```python
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='library/search.html')),
    path('search/', TemplateView.as_view(template_name='library/search.html')),
    path('upload/', TemplateView.as_view(template_name='library/upload.html')),
    path('admin-panel/', TemplateView.as_view(template_name='library/admin.html')),
]
```

> Django's `APPEND_SLASH = True` default means requests to `/search`, `/upload`, and `/admin-panel` (without trailing slash) are redirected to their trailing-slash equivalents automatically.

## Database Layer

The database will use SQLite and have the following table:

### MdLibrary Table

| Column | SQLite Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | — | Surrogate key; single-column PK is required for Django ORM compatibility |
| `file_name` | `TEXT` | `NOT NULL` | — | Max 255 characters, enforced at the API layer |
| `file_version` | `INTEGER` | `NOT NULL`, `CHECK (file_version >= 1)` | `1` | Incremented each time a file with the same name is uploaded |
| `file_contents` | `TEXT` | `NOT NULL` | — | Raw markdown content; max size enforced at the API layer per `max_upload_bytes` in `mdviewer.yaml` |
| `deleted` | `INTEGER` | `NOT NULL`, `CHECK (deleted IN (0, 1))` | `0` | Soft-delete flag. SQLite has no native BOOLEAN — stored as `0` (false) or `1` (true). Django's `BooleanField` handles this transparently. |
| `created_at` | `TEXT` | `NOT NULL` | Current UTC timestamp | ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`). SQLite has no native DATETIME — Django's `DateTimeField` with `auto_now_add=True` handles storage and population automatically. |
| `updated_at` | `TEXT` | `NOT NULL` | Current UTC timestamp | Updated on every write. Django's `DateTimeField` with `auto_now=True` handles this automatically. |

### Constraints and Indexes

* **UNIQUE constraint** on `(file_name, file_version)` — enforces the versioning invariant at the database level, not just in application logic.
* **Index** on `file_name` — the primary search operation filters by `file_name`; this index prevents full table scans.

Implement these in the Django model's `Meta` class:

```python
class Meta:
    db_table = 'mdlibrary'
    constraints = [
        models.UniqueConstraint(fields=['file_name', 'file_version'], name='unique_file_name_version'),
    ]
    indexes = [
        models.Index(fields=['file_name'], name='idx_file_name'),
    ]
```

### Versioning Behavior

If a file is uploaded with the same name as an existing record, the version is incremented from the highest existing `file_version` for that `file_name`. The first upload of any file name starts at version `1`.

### Soft Delete

The `deleted` column is used for soft delete and defaults to `0` (not deleted). When set to `1`, the record is considered deleted and excluded from normal search results. Records are never physically removed from the database.

### File Size Limit

`TEXT` in SQLite has no database-level size limit. The maximum allowed file size is read from `max_upload_bytes` in `mdviewer.yaml` and enforced in the API layer at upload time to prevent performance degradation and excessive disk usage.

## YAML Configuration File

The YAML configuration file (`mdviewer.yaml`) lives in the project root directory and is loaded once at Django startup. Add the following block at the top of `mdviewer/settings.py`, before any setting that depends on it, so the loaded values are available to `DATABASES`, `LOGGING`, and other settings:

```python
import os
import yaml

with open(BASE_DIR / 'mdviewer.yaml') as _f:
    YAML_CONFIG = yaml.safe_load(_f)
```

**Configuration keys:**

| Key | Type | Description |
|---|---|---|
| `database_path` | string | Path to the SQLite database file, relative to the project root. Used for `DATABASES['default']['NAME']`. The parent directory must exist before the app starts — Django will not create it automatically. |
| `log_directory` | string | Directory for log files, relative to the project root. Used for the `LOGGING` handler filename. The directory must exist before the app starts. |
| `log_level` | string | Logging level for the `library` logger. Accepted values: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Used in the `LOGGING` dict. |
| `debug` | boolean | Sets Django's `DEBUG` setting. Must be `false` in production. |
| `allowed_hosts` | list of strings | Sets Django's `ALLOWED_HOSTS`. List the hostnames and IP addresses the app will be served from. |
| `max_upload_bytes` | integer | Maximum allowed size of `file_contents` in bytes. Used in both the API layer validation and `DATA_UPLOAD_MAX_MEMORY_SIZE` (set to `max_upload_bytes + 100000` to account for request overhead). |

> **Note on `SECRET_KEY`:** The Django secret key must not be stored in `mdviewer.yaml` — YAML files can be accidentally committed to source control. Read `SECRET_KEY` from the `DJANGO_SECRET_KEY` environment variable only.

**Example `mdviewer.yaml`:**

```yaml
database_path: db/mdviewer.db
log_directory: logs
log_level: INFO
debug: true  # Use false only in production; Django's runserver does not serve static files when DEBUG is false
allowed_hosts:
  - localhost
  - 127.0.0.1
max_upload_bytes: 1048576  # 1 MB
```

## ORM/API Layer

The ORM/API layer consists of objects and CRUD operations for transferring data between API calls and the SQLite database. All endpoints are implemented using DjangoRestFramework.

### ORM/API Security Considerations

Reference the OWASP API Security Top 10 when designing and implementing security for the API/ORM layer. The specific requirements below must be implemented.

#### SQL Injection

* All database interaction must use the Django ORM's parameterized query methods (e.g., `.filter()`, `.get()`, `.create()`).
* Raw SQL (`Model.objects.raw()`, `connection.execute()`, f-strings in query construction) is **prohibited**. If raw SQL is ever required, Django's parameterized `execute(sql, params)` form must be used — never string formatting or f-strings.
* The `file_name` partial-match search must use `.filter(file_name__icontains=value)`, not a raw `LIKE` string.

#### Markdown Rendering and XSS Prevention

The rendering pipeline for stored markdown must follow this exact order — deviating from this order creates XSS vulnerabilities:

1. **Store raw markdown as-is.** Raw markdown text is plain text and is safe to store in the database without modification. Do not apply nh3 to raw markdown at upload time — nh3 sanitizes HTML, not markdown.
2. **At retrieval time (`GET /api/v1/library/{id}/`), render markdown to HTML** using python-markdown with the following extensions enabled:
   - `fenced_code` — enables fenced code blocks (` ``` ` syntax).
   - `codehilite` — applies Pygments syntax highlighting to code blocks. Configure with `css_class='highlight'` and `guess_lang=False`.
   - `tables` — enables GFM-style pipe tables.
   - `nl2br` — converts single newlines to `<br>` tags for more natural line break handling.

   Pygments generates inline `<span>` elements with CSS class names (e.g., `.highlight`, `.k`, `.s`). The Pygments CSS stylesheet must be included in the base HTML template. Generate the CSS by running: `python -c "from pygments.formatters import HtmlFormatter; print(HtmlFormatter(style='default').get_style_defs('.highlight'))"` and save it to `library/static/library/css/pygments.css`. Load it in the base template with a `<link>` tag. The `codehilite` CSS class names (`highlight`, `k`, `s`, etc.) are allowed via the `'*': {'class'}` wildcard in the nh3 `attributes` configuration so Pygments styling is not stripped.

3. **Disable raw HTML passthrough** in python-markdown. By default, python-markdown passes raw HTML blocks (e.g., `<script>` tags, inline event handlers) directly into the rendered output before nh3 sees them. Note: `safe_mode` was removed in python-markdown 3.0 and must not be used. Instead, create the `Markdown` instance and then deregister the `html_block` preprocessor before calling `convert()`:

   ```python
   md = markdown.Markdown(
       extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'],
       extension_configs={'codehilite': {'css_class': 'highlight', 'guess_lang': False}},
   )
   md.preprocessors.deregister('html_block')
   rendered = md.convert(file_contents)
   md.reset()  # reset state if the instance is reused across requests
   ```

   This is defense-in-depth; nh3 (step 4) remains the primary XSS sanitization layer.
4. **Apply nh3 to the rendered HTML output** with a strict allowlist (see below) to strip any disallowed tags and attributes before the result is returned as `rendered_html`.

**nh3 sanitization:**

Allowed tags: `a`, `abbr`, `b`, `blockquote`, `br`, `code`, `del`, `div`, `em`, `h1`, `h2`, `h3`, `h4`, `h5`, `h6`, `hr`, `i`, `img`, `li`, `ol`, `p`, `pre`, `span`, `strong`, `table`, `tbody`, `td`, `th`, `thead`, `tr`, `ul`

> `div` and `span` are required for Pygments/codehilite output. The `codehilite` extension wraps highlighted code in `<div class="highlight">` and uses `<span class="k">`, `<span class="s">`, etc. for individual tokens. Without these tags in the allowlist, nh3 strips them and all syntax highlighting is lost.

Allowed attributes:
* `a`: `href` (schemes restricted to `http` and `https` via `url_schemes`; relative paths are always permitted), `title`
* `img`: `src` (schemes restricted to `http` and `https` via `url_schemes` — data URIs are rejected), `alt`, `title`
* All other tags: `class` only (required for Pygments CSS class names on `div` and `span` elements)

**nh3.clean() call:** nh3 handles protocol filtering natively via `url_schemes` — no callable needed. Disallowed tags are stripped by default. Relative URLs (no URL scheme) are always permitted regardless of `url_schemes`:

```python
import nh3

rendered_html = nh3.clean(
    rendered,
    tags={
        'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'del', 'div', 'em',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol',
        'p', 'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul',
    },
    attributes={
        'a':   {'href', 'title'},
        'img': {'src', 'alt', 'title'},
        '*':   {'class'},   # wildcard — allows class on all tags (required for Pygments spans and divs)
    },
    url_schemes={'http', 'https'},   # relative paths (no scheme) are always permitted
    strip_comments=True,
)
```

**`mark_safe()` prohibition:** Django's `mark_safe()` must never be called on any string derived from user-supplied content unless it has first been processed through the full rendering pipeline above (python-markdown → nh3). Calling `mark_safe()` on unprocessed input is a critical XSS vulnerability.

#### Rate Limiting

All endpoints must implement DRF's `AnonRateThrottle` since no authentication is required. Rate limit violations must return `429 Too Many Requests`. Suggested per-endpoint limits:

| Endpoint | Limit |
|---|---|
| `POST /api/v1/library/` | 10 requests/minute (writes up to 1 MB) |
| `PATCH /api/v1/library/{id}/` | 20 requests/minute |
| `DELETE /api/v1/library/{id}/` | 20 requests/minute |
| `GET /api/v1/library/` | 60 requests/minute |
| `GET /api/v1/library/{id}/` | 60 requests/minute |
| `GET /api/v1/library/stats/` | 30 requests/minute |

**Implementation pattern:** Create one throttle class per endpoint in `library/throttles.py` by subclassing `AnonRateThrottle` and overriding `scope`. Register each scope in `DEFAULT_THROTTLE_RATES` in `settings.py`. Apply to a view via `throttle_classes`:

```python
# library/throttles.py
from rest_framework.throttling import AnonRateThrottle

class LibraryCreateThrottle(AnonRateThrottle):
    scope = 'library_create'

class LibraryListThrottle(AnonRateThrottle):
    scope = 'library_list'

# ... one class per endpoint
```

```python
# In REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] in settings.py:
'library_create': '10/minute',
'library_list': '60/minute',
# ... all scopes listed here
```

```python
# On the view:
class LibraryListCreateView(APIView):
    def get_throttles(self):
        if self.request.method == 'POST':
            return [LibraryCreateThrottle()]
        return [LibraryListThrottle()]
```

#### HTTP Security Headers

Enable Django's `SecurityMiddleware` and configure the following headers on all responses:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' ajax.googleapis.com; style-src 'self' ajax.googleapis.com cdn.jsdelivr.net fonts.googleapis.com; font-src fonts.gstatic.com cdn.jsdelivr.net; img-src 'self' https: data:; frame-ancestors 'none'` |

#### Input Validation — File Name

`file_name` must be validated at the API layer on POST (and wherever received), not only in the browser form. Accepted characters: alphanumeric (`A–Z`, `a–z`, `0–9`), hyphens (`-`), underscores (`_`), and dots (`.`). Maximum 255 characters. Any other characters, path separators (`/`, `\`), or spaces must be rejected with `400 MISSING_PARAMETER`.

#### Request Size Enforcement

Set Django's `DATA_UPLOAD_MAX_MEMORY_SIZE` to `max_upload_bytes + 100,000` (read from `mdviewer.yaml`) to reject oversized request bodies before they reach the view layer. The extra headroom accounts for request envelope overhead beyond the raw file content.

#### Error Response Sanitization

`500` responses must never include stack traces, internal file paths, ORM query details, or Django version information. The `error` field in all `500` responses must contain only a generic message: `"An internal server error occurred."`. Full exception details must be written to the server-side log only.

#### Security Event Logging

The following events must be written to the application log:
* Rate limit violations: endpoint, timestamp, and client IP address.
* Validation failures (`400` responses): the field name that failed validation — **never** the field's value, which may contain attack payloads.
* All `500` errors: full exception and stack trace (server log only, never in API response).
* File uploads: `file_name` and resulting `file_version` — **never** log `file_contents`.

### URL Structure

All API endpoints are prefixed with `/api/v1/` to separate API routes from page routes and to support future versioning. Trailing slashes follow Django REST Framework convention.

| Method | URL | Operation |
|---|---|---|
| `GET` | `/api/v1/library/` | Search / list records (collection) |
| `POST` | `/api/v1/library/` | Create a new record |
| `GET` | `/api/v1/library/{id}/` | Retrieve a single record with full content |
| `PATCH` | `/api/v1/library/{id}/` | Partially update a record |
| `DELETE` | `/api/v1/library/{id}/` | Soft-delete a record |
| `GET` | `/api/v1/library/stats/` | Retrieve database statistics |

`{id}` is the integer surrogate primary key of the MdLibrary record.

No endpoint requires authentication.

### Serializer Design

Two DRF serializers are required for the `MdLibrary` model:

* **`MdLibraryMetaSerializer`** — returns all fields *except* `file_contents` and `rendered_html`. Used for: collection responses (`GET /api/v1/library/`), create responses (`POST`), and update responses (`PATCH`).

* **`MdLibraryDetailSerializer`** — returns all metadata fields plus `file_contents` and `rendered_html`. `rendered_html` is not a database column; implement it as a `SerializerMethodField` that runs the full markdown rendering pipeline (python-markdown → nh3) on `file_contents` at serialization time. Used for single-record responses (`GET /api/v1/library/{id}/`).

### HTTP Status Codes

HTTP status codes are the primary mechanism for signaling success or failure. All responses also include a `status` string field in the JSON body as a convenience supplement.

| HTTP Code | Meaning | `status` value |
|---|---|---|
| `200 OK` | Request succeeded, data returned | `SUCCESS` |
| `201 Created` | Record successfully created | `SUCCESS` |
| `204 No Content` | Soft-delete succeeded (no body) | — |
| `400 Bad Request` | Missing or invalid parameter | `MISSING_PARAMETER` |
| `404 Not Found` | Record not found | `NO_RESULTS` |
| `429 Too Many Requests` | Rate limit exceeded | `RATE_LIMITED` |
| `500 Internal Server Error` | Unhandled server or database error | `FAILURE` |

### JSON Response Schema

**Collection response** (`GET /api/v1/library/`) — metadata only, no `file_contents`:
```json
{
  "status": "SUCCESS",
  "count": 2,
  "results": [
    {
      "id": 1,
      "file_name": "example.md",
      "file_version": 1,
      "deleted": false,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Single record response** (`GET /api/v1/library/{id}/`) — includes full content and server-rendered HTML:
```json
{
  "status": "SUCCESS",
  "result": {
    "id": 1,
    "file_name": "example.md",
    "file_version": 1,
    "file_contents": "# Hello\nThis is markdown.",
    "rendered_html": "<h1>Hello</h1><p>This is markdown.</p>",
    "deleted": false,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:22:00Z"
  }
}
```

**Error response** (all methods on failure):
```json
{
  "status": "MISSING_PARAMETER",
  "error": "file_name is required and must not be blank."
}
```

**Create response** (`POST /api/v1/library/`) — `201 Created`, metadata only (no `file_contents` or `rendered_html`). Response also includes a `Location` header pointing to `/api/v1/library/{id}/`:
```json
{
  "status": "SUCCESS",
  "result": {
    "id": 3,
    "file_name": "example.md",
    "file_version": 2,
    "deleted": false,
    "created_at": "2025-03-01T09:00:00Z",
    "updated_at": "2025-03-01T09:00:00Z"
  }
}
```

**Update response** (`PATCH /api/v1/library/{id}/`) — `200 OK`, metadata only (no `file_contents` or `rendered_html`):
```json
{
  "status": "SUCCESS",
  "result": {
    "id": 3,
    "file_name": "example.md",
    "file_version": 2,
    "deleted": true,
    "created_at": "2025-03-01T09:00:00Z",
    "updated_at": "2025-03-01T09:15:00Z"
  }
}
```

**Rate limit response** (`429 Too Many Requests`):
```json
{
  "status": "RATE_LIMITED",
  "error": "Request rate limit exceeded. Please wait before retrying."
}
```

**Stats response** (`GET /api/v1/library/stats/`):
```json
{
  "status": "SUCCESS",
  "active_files": 12,
  "total_records": 31,
  "deleted_records": 7
}
```

### Endpoint Specifications

#### GET /api/v1/library/ — Search Records

Searches the MdLibrary table and returns matching records as metadata (no `file_contents`).

**Query parameters:**

| Parameter | Required | Description |
|---|---|---|
| `file_name` | No | Case-insensitive partial match (`LIKE '%value%'`). If provided, must not be blank — return `400 MISSING_PARAMETER` if the parameter is present but empty. If omitted entirely, no file name filter is applied (all records are eligible). |
| `deleted` | No | Filter by deleted status. Accepts `true` or `false`. If omitted, no deleted filter is applied (all records returned regardless of deleted status). |

**Behavior:**
- If `file_name` is provided but blank, return `400 MISSING_PARAMETER`.
- Apply filters for any parameters that are present: `file_name` as a case-insensitive partial match, `deleted` as an exact boolean match.
- Order results by `file_name` ascending, then `file_version` descending (so the newest version of each file appears first within its name group).
- Return `200 SUCCESS` with the matching records and a `count`. `results` may be an empty list if no records match — this is not an error.
- Return `500 FAILURE` on any unhandled exception.

---

#### POST /api/v1/library/ — Create a Record

Creates a new MdLibrary record. If a record with the same `file_name` already exists, a new version is created by incrementing the highest existing `file_version` for that name.

**Request body (JSON):**

| Field | Required | Validation |
|---|---|---|
| `file_name` | Yes | Not blank; max 255 characters; only alphanumeric characters, hyphens, underscores, and dots. |
| `file_contents` | Yes | Not blank; at least one non-whitespace character; max size per `max_upload_bytes` in `mdviewer.yaml`. |

**Behavior:**
- Validate both fields. Return `400 MISSING_PARAMETER` with a descriptive `error` message if either is missing, blank, or invalid. Validate `file_name` against the allowed character set (alphanumeric, hyphens, underscores, dots; max 255 characters).
- Store `file_contents` as raw markdown text without modification. Do not apply nh3 at upload time — nh3 sanitization runs at retrieval time during HTML rendering only.
- Determine the new `file_version`: query for **all** records with the same `file_name` **regardless of `deleted` status**, ordered by `file_version` descending. If found, increment the highest version. If not found, use version `1`. Including deleted records is required — excluding them would allow a re-upload of a previously deleted file name to produce a duplicate version number, violating the `UNIQUE(file_name, file_version)` constraint.
- Create the record. Return `201 Created` with the full created record in the response body and a `Location` header pointing to `/api/v1/library/{id}/`.
- Return `500 FAILURE` on any unhandled exception.

---

#### GET /api/v1/library/{id}/ — Retrieve a Single Record

Retrieves one MdLibrary record by its `id`, including full `file_contents` and server-rendered `rendered_html`.

**Behavior:**
- Look up the record by `id`. Return `404 NO_RESULTS` if not found. Deleted records are returned normally — this endpoint does not filter by `deleted` status. A `404` is returned only when the `id` does not exist in the database.
- Produce `rendered_html` by following the rendering pipeline exactly:
  1. Pass `file_contents` to python-markdown with raw HTML passthrough disabled (embedded HTML treated as escaped text).
  2. Pass the resulting HTML to nh3 with the configuration defined in the Security Considerations section.
- Return `200 SUCCESS` with the full record including both `file_contents` (raw) and `rendered_html` (sanitized HTML).
- Return `500 FAILURE` on any unhandled exception.

---

#### PATCH /api/v1/library/{id}/ — Partially Update a Record

Updates one or more fields on an existing MdLibrary record. Only fields included in the request body are updated.

**Request body (JSON) — at least one field required:**

| Field | Description |
|---|---|
| `file_contents` | New raw markdown content. Stored as-is; nh3 sanitization runs at retrieval time only. Max size per `max_upload_bytes` in `mdviewer.yaml`. |
| `deleted` | Boolean. Set to `true` to soft-delete; `false` to restore. |

**Behavior:**
- Look up the record by `id`. Return `404 NO_RESULTS` if not found.
- Validate that at least one of `file_contents` or `deleted` is present. Return `400 MISSING_PARAMETER` if the body is empty or contains neither field.
- Apply only the supplied fields. `updated_at` is updated automatically.
- Return `200 SUCCESS` with the updated record.
- Return `500 FAILURE` on any unhandled exception.

---

#### DELETE /api/v1/library/{id}/ — Soft-Delete a Record

Sets `deleted = true` on the specified record. Records are never physically removed from the database.

**Behavior:**
- Look up the record by `id`. Return `404 NO_RESULTS` if not found.
- Set `deleted = true` and save. Return `204 No Content` on success.
- Return `500 FAILURE` on any unhandled exception.

---

#### GET /api/v1/library/stats/ — Database Statistics

Returns aggregate counts used by the Admin page.

**Behavior:**
- Query and return:
  - `active_files` — count of distinct `file_name` values where at least one record has `deleted = false`.
  - `total_records` — count of all rows regardless of `deleted`.
  - `deleted_records` — count of rows where `deleted = true`.
- Return `200 SUCCESS` with the stats object.
- Return `500 FAILURE` on any unhandled exception.

## Web Frontend

Browser AJAX calls should always call the Django ORM/API layer. All calls to external web services, APIs, or to the SQLite database will be made through and from the Django ORM/API layer, never from the browser html/javascript.

### Web Frontend Security

#### CSRF Token Handling

Django's CSRF protection is enabled by default and applies to all non-GET AJAX calls (POST, PATCH, DELETE). jQuery AJAX calls must include the CSRF token in the `X-CSRFToken` request header on every state-changing request. The token value is read from the `csrftoken` browser cookie. Configure jQuery's `$.ajaxSetup()` in the base template to send this header automatically on all non-GET requests.

#### DOM Injection

JavaScript must never use `.html()`, `innerHTML`, or equivalent methods to insert user-supplied data (file names, error messages, API response strings) into the DOM. Use `.text()` or `textContent` for all user-supplied string values. The sole exception is `rendered_html` from `GET /api/v1/library/{id}/`, which has been sanitized server-side by the python-markdown → nh3 pipeline and may be injected into the rendered content `<div>` using `.html()` only — no other field may use `.html()`.

The Django web app should use a base template for all pages that includes links to the javascript libraries and displays a common header with the site name "MD Viewer" at the top left in italics. The base template must include `{% load static %}` at the top to enable the `{% static %}` template tag. Load the Pygments CSS using `<link rel="stylesheet" href="{% static 'library/css/pygments.css' %}">` in the HEAD.

### Web UI Color Scheme

The UI should use the standard color scheme that comes with Bootstrap and use Bootstrap to toggle between light mode and dark mode. The default mode is dark mode. When the web UI loads, read the user's preference from browser local storage. If no preference has been stored, default to dark mode. When the user toggles light/dark mode, save the updated preference to browser local storage so it persists across page loads and sessions.

### Frontend Web Libraries

The web frontend uses libraries linked via CDN. Load them in the HTML HEAD tag in the order shown below. **Script loading order matters:** jQuery must be loaded before Bootstrap-Table JS, which depends on it.

CSS (order among these is not significant):
* Bootstrap CSS
  - <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/bootstrap/5.3.3/css/bootstrap.min.css">
* Bootstrap-Table CSS
  - <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/bootstrap-table/1.23.2/dist/bootstrap-table.min.css">
* Bootstrap-Icons
  - <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/bootstrap-icons.min.css">

Scripts (must be loaded in this order):
* jQuery — **load first**; Bootstrap-Table requires jQuery to be present at initialization
  - <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
* Bootstrap JS
  - <script src="https://ajax.googleapis.com/ajax/libs/bootstrap/5.3.3/js/bootstrap.min.js"></script>
* Bootstrap-Table JS
  - <script src="https://ajax.googleapis.com/ajax/libs/bootstrap-table/1.23.2/dist/bootstrap-table.min.js"></script>

* The web frontend uses Google fonts. Preconnect to the Google Fonts library using these links:
  - <link rel="preconnect" href="https://fonts.googleapis.com">
  - <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

* Use the following tags in the HTML HEAD tag to load the following fonts:
  - <link href="https://fonts.googleapis.com/css2?family=Workbench&display=swap" rel="stylesheet">
  - <link href="https://fonts.googleapis.com/css2?family=TASA+Orbiter:wght@400..800&display=swap" rel="stylesheet">


### Common Header and Fonts
The common header should use the Workbench font at 48px size for the site title. Everything else on the site should use the TASA Orbiter font with a size appropriate for the usage in the UI. The common header should include a light/dark mode toggle button using Bootstrap's color mode functionality. When the user toggles light/dark mode, store the updated setting in browser local storage. No login or logout functionality is required.

### Navigation Bar

The base template includes a Bootstrap navbar below the common header. The navbar contains links to each page. The link for the currently active page is highlighted using Bootstrap's `active` class. Nav links:

* Search — navigates to `/search`
* Upload — navigates to `/upload`
* Admin — navigates to `/admin-panel`

Use `/admin-panel` as the URL for the admin page to avoid conflicting with Django's built-in `/admin` route.

---

### List of Pages

The web frontend uses Django to display dynamic HTML and consists of the following pages:

* Search page — search the library by file name and view a selected file
* Upload page — upload a new markdown file
* Admin page — view database statistics and manage (delete/undelete) records

---

### Search Page

**URL:** `/search` — also serves as the default home page at `/`

**Purpose:** Find markdown files in the library by name and view their contents.

**Layout:** Search form at top, results table in the middle, tab bar and tab content area at the bottom (tab area is hidden until at least one file is opened).

#### Search Form

| Control | Type | Required | Validation |
|---|---|---|---|
| File Name | text input | Yes | Must not be blank; max 255 characters |
| Search | submit button | — | Disabled while AJAX call is in progress |
| Clear | button | — | Clears the input and resets the results table |

* The File Name input accepts partial matches. The AJAX GET call to `/api/v1/library/` passes the value as the `file_name` query parameter and always includes `deleted=false` to restrict results to active records only.
* Placeholder text: `Enter file name to search`
* On submit, validate client-side that the input is not blank. If blank, display a Bootstrap `is-invalid` indicator with the message "File name is required."

#### Results Table

* Rendered using Bootstrap-Table.
* Columns: **File Name** (sortable), **Version** (sortable, numeric), **Actions**.
* Each table row must have a `data-id` attribute set to the record's `id` value from the API response. This attribute is how the View button identifies which record to fetch.
* Actions column contains a **View** button (icon: `bi-eye`) for each row. The View button's click handler reads the `data-id` attribute from its parent row to determine the record `id`, then calls `GET /api/v1/library/{id}/` to load the file content. Clicking View opens the file in a new in-page tab in the Tab Area below the results table (this is a DOM tab, not a browser tab). If the file (same `id`) is already open in a tab, clicking View switches focus to that existing tab instead of opening a duplicate.
* If the API returns an empty `results` list, display the message "No files found matching that name." in the table body.
* If the API returns `400` or `500`, display a red dismissible Bootstrap alert above the table.
* If the API returns `429 Too Many Requests`, display a red dismissible Bootstrap alert above the table: `"Too many requests. Please wait a moment and try again."`

#### Tab Area

* Hidden on page load. Becomes visible when the first file tab is opened.
* Consists of two parts:
  1. **Tab Bar** — a horizontal row of tabs, one per open file.
  2. **Tab Content Area** — the content pane below the tab bar, showing the active tab's file contents.

**Tab Bar:**
* Each tab displays the file name and version number: e.g., `my-document.md v2`
* Each tab has a **Close** button (icon: `bi-x`, displayed inline on the tab) that closes that tab.
* The active tab is highlighted using Bootstrap's active tab styling.
* Clicking an inactive tab makes it the active tab and shows its content in the Tab Content Area.
* When the last open tab is closed, the entire Tab Area is hidden again.
* Opening a file that is already open (same `id`) switches focus to its existing tab rather than creating a duplicate.

**Tab Content Area:**
* Displays the content of the currently active tab.
* Each tab's content area contains:
  * A heading showing the file name and version: e.g., `my-document.md — Version 2`
  * Two toggle buttons to switch view mode:
    * **Rendered** (default) — sanitized HTML output from python-markdown and nh3, displayed inside a styled `<div>`.
    * **Raw Markdown** — raw markdown text displayed inside a `<pre>` block using a monospace font.
  * Each tab independently tracks its own Rendered/Raw toggle state.
* Tab content is loaded via AJAX GET to `/api/v1/library/{id}/` using the record's `id` when the tab is first opened. The response includes both `file_contents` (raw markdown) and `rendered_html` (server-rendered and sanitized HTML), so no second request is needed to switch between view modes. The result is cached in the DOM so switching between tabs does not re-fetch from the server.
* If the AJAX call fails, display a red dismissible alert inside the tab content area with the status value.

---

### Upload Page

**URL:** `/upload`

**Purpose:** Upload a new markdown file (or a new version of an existing file) to the library.

**Layout:** A single centered form card on the page.

#### Upload Form

| Control | Type | Required | Validation |
|---|---|---|---|
| File Name | text input | Yes | Not blank; max 255 characters; only alphanumeric characters, hyphens (`-`), underscores (`_`), and dots (`.`). No path separators or spaces. |
| Select File | file input | No | Accepts `.md` and `.txt` files only (`accept=".md,.txt"`). Selecting a file auto-populates the File Name input and loads the file contents into the Markdown Content textarea using the browser FileReader API. |
| Markdown Content | textarea | Yes | Not blank; min 1 non-whitespace character. Rows: 15. Monospace font. |
| Upload | submit button | — | Disabled while submission is in progress. |
| Clear | button | — | Resets all form fields to empty. |

* Placeholder for File Name: `e.g. my-document.md`
* Placeholder for Markdown Content: `Paste or type markdown content here, or select a .md file above.`
* Client-side validation runs before the AJAX call. Invalid fields are highlighted with the Bootstrap `is-invalid` class; a descriptive error message appears below each invalid field.
* The form submits via AJAX POST to `/api/v1/library/`.

#### Feedback After Submission

* **New file (first version):** API returns `201 Created`. Display a green dismissible alert: `"[file name]" was uploaded successfully as version 1.`
* **New version (file name already existed):** API returns `201 Created`. Display a blue informational alert: `A new version (v[N]) of "[file name]" was created.` The new version number is read from the `file_version` field in the response body.
* Both cases return `201 Created`. Determine which alert to show by checking `file_version` in the response body: if `file_version === 1`, show the green new-file alert; if `file_version > 1`, show the blue new-version alert.
* **400 or 500:** Display a red dismissible alert with the `error` field from the response body.
* **429 Too Many Requests:** Display a red dismissible alert: `"Too many requests. Please wait a moment before uploading again."`
* After a successful upload, clear the form fields so another file can be uploaded.

---

### Admin Page

**URL:** `/admin-panel`

**Purpose:** View database statistics and manage file records (soft delete and undelete).

**Layout:** Stats cards row at the top, filter controls below, records table at the bottom.

#### Database Statistics

Displayed as a Bootstrap card row loaded via AJAX GET to `/api/v1/library/stats/` on page load. Three stat cards:

| Stat | Description |
|---|---|
| Active Files | Count of distinct file names where at least one non-deleted version exists |
| Total Records | Count of all rows in MdLibrary regardless of deleted status |
| Deleted Records | Count of rows where `deleted = true` |

#### Initial Page Load

On page load:
1. Load the stats cards via AJAX GET to `/api/v1/library/stats/`.
2. Load the records table via AJAX GET to `/api/v1/library/?deleted=false`. The **Active Only** filter button is pre-selected (highlighted) by default.

#### Filter Controls

A row of Bootstrap toggle buttons above the records table to control which records are shown. Only one filter button is active at a time. Clicking a filter button makes a new server-side API call and replaces the current table contents with the response.

| Button | API Call | Behavior |
|---|---|---|
| Active Only (default) | `GET /api/v1/library/?deleted=false` | Shows records where `deleted = false` |
| Deleted Only | `GET /api/v1/library/?deleted=true` | Shows records where `deleted = true` |
| All Records | `GET /api/v1/library/` (no deleted param) | Shows all records |

* A text input next to the toggle buttons provides **client-side** filtering of the currently visible table rows by file name (no additional API call). Placeholder: `Filter by file name`

#### Records Table

* Rendered using Bootstrap-Table.
* Columns: **File Name** (sortable), **Version** (sortable, numeric), **Status**, **Actions**.
* Each table row must have the following data attributes set from the API response:
  * `data-id` — the record's `id` value. Used by all action button handlers to identify the record in API calls.
  * `data-file-name` — the record's `file_name` value. Used to populate the delete confirmation modal body.
  * `data-file-version` — the record's `file_version` value. Used to populate the delete confirmation modal body.
* **Status** column displays `Active` or `Deleted` as a Bootstrap badge (green for Active, red for Deleted).
* **Actions** column per row:
  * If the record is Active: a **Delete** button (red, icon: `bi-trash`)
  * If the record is Deleted: an **Undelete** button (green, icon: `bi-arrow-counterclockwise`)

#### Delete Action

* Clicking **Delete** opens a Bootstrap confirmation modal before any API call is made.
  * Modal title: `Confirm Delete`
  * Modal body: `Are you sure you want to delete "[file name]" version [N]? This action can be undone.`
  * Modal buttons: **Cancel** (dismisses modal) and **Delete** (red, proceeds with deletion).
* On confirmation, send AJAX DELETE to `/api/v1/library/{id}/` using the record's `id`.
* On `204 No Content`: update the row's Status badge to `Deleted` and replace the Delete button with an Undelete button. Refresh the stats cards.
* On `404` or `500`: dismiss the modal and display a red dismissible alert above the table.
* On `429 Too Many Requests`: dismiss the modal and display a red dismissible alert above the table: `"Too many requests. Please wait a moment before trying again."`

#### Undelete Action

* Clicking **Undelete** requires no confirmation dialog.
* Send AJAX PATCH to `/api/v1/library/{id}/` with `{"deleted": false}` using the record's `id`.
* On `200 OK`: update the row's Status badge to `Active` and replace the Undelete button with a Delete button. Refresh the stats cards.
* On `404` or `500`: display a red dismissible alert above the table.
* On `429 Too Many Requests`: display a red dismissible alert above the table: `"Too many requests. Please wait a moment before trying again."`
