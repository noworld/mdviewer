# MD Viewer — Database DDL Specification

This file contains the SQLite DDL required to create the MD Viewer database schema.

> **Note on Django migrations:** Django manages the database schema through its migration system. Running `python manage.py migrate` will generate this schema automatically from the model definition. The DDL below represents the equivalent raw SQL, useful for documentation, review, and manual inspection. The Django app is named `library`, so Django's default table naming convention would produce `library_mdlibrary` — override this by setting `db_table = 'mdlibrary'` in the model's `Meta` class.

---

## Create Table

```sql
CREATE TABLE IF NOT EXISTS mdlibrary (
    id           INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    file_name    TEXT    NOT NULL,
    file_version INTEGER NOT NULL DEFAULT 1,
    file_contents TEXT   NOT NULL,
    deleted      INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    CONSTRAINT chk_mdlibrary_file_version CHECK (file_version >= 1),
    CONSTRAINT chk_mdlibrary_deleted      CHECK (deleted IN (0, 1)),
    CONSTRAINT uq_mdlibrary_file_name_version UNIQUE (file_name, file_version)
);
```

---

## Create Index

```sql
CREATE INDEX IF NOT EXISTS idx_mdlibrary_file_name
    ON mdlibrary (file_name);
```

---

## Column Reference

| Column | SQLite Type | Nullable | Default | Constraint(s) |
|---|---|---|---|---|
| `id` | `INTEGER` | No | — | `PRIMARY KEY AUTOINCREMENT` |
| `file_name` | `TEXT` | No | — | `UNIQUE` with `file_version` |
| `file_version` | `INTEGER` | No | `1` | `CHECK (file_version >= 1)`, `UNIQUE` with `file_name` |
| `file_contents` | `TEXT` | No | — | — |
| `deleted` | `INTEGER` | No | `0` | `CHECK (deleted IN (0, 1))` |
| `created_at` | `TEXT` | No | Current UTC timestamp | — |
| `updated_at` | `TEXT` | No | Current UTC timestamp | — |

---

## Notes

### Primary Key
`id` is a surrogate auto-incrementing integer primary key. The natural composite key `(file_name, file_version)` is enforced as a `UNIQUE` constraint rather than the primary key, which is required for Django ORM compatibility.

### Boolean Storage
SQLite has no native `BOOLEAN` type. The `deleted` column is stored as `INTEGER` (`0` = false, `1` = true). The `CHECK` constraint restricts values to only `0` or `1`. Django's `BooleanField` maps this transparently.

### Datetime Storage
SQLite has no native `DATETIME` type. The `created_at` and `updated_at` columns are stored as `TEXT` in ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`). The `DEFAULT` expression uses SQLite's `strftime` function to populate the value on direct SQL insert. When using Django:
- `created_at` uses `DateTimeField(auto_now_add=True)` — set automatically on first save.
- `updated_at` uses `DateTimeField(auto_now=True)` — updated automatically on every save.
- Django sets these values in Python before the SQL statement is issued, so the `DEFAULT` expression acts as a safety net for direct SQL inserts only.

### File Name Validation
The `file_name` column has no character-level `CHECK` constraint in SQLite. Valid file name characters (alphanumeric, hyphens, underscores, dots; max 255 characters; no path separators or spaces) are enforced in the API layer at upload time.

### File Size Limit
The `file_contents` column is `TEXT` with no database-level size restriction. The maximum allowed file size is read from `max_upload_bytes` in `mdviewer.yaml` and enforced in the API layer at upload time.

### Soft Delete
Records are never physically deleted. The `deleted` column is set to `1` to mark a record as deleted and `0` to restore it. Queries for active records must filter on `deleted = 0`.

### Index Strategy
A single-column index on `file_name` supports the primary search pattern (`WHERE file_name = ?` or `WHERE file_name LIKE ?`). The `UNIQUE` constraint on `(file_name, file_version)` implicitly creates a compound index that also supports queries filtering on both columns.
