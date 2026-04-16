# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Data Tables API — a Flask REST API for creating tables with dynamic schemas, storing rows as JSON-in-SQLite, and querying with filtering/pagination. No auth, no frontend.

## Commands

```bash
# Run dev server (port 3000)
source venv/bin/activate
python run.py

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_tables.py -v
python -m pytest tests/test_rows.py -v

# Run a single test
python -m pytest tests/test_rows.py::test_name -v

# Docker
./startup.sh                # build & run (requires Colima)
docker compose down         # stop
```

## Architecture

**App factory pattern:** `create_app()` in `app/__init__.py` builds the Flask app, initializes the DB, and registers blueprints.

**Database layer** (`app/database.py`): Manages SQLite connections via Flask's `g` object. Three SQL tables: `tables`, `columns`, `rows`. Row data is stored as a JSON string in `rows.data` — schema changes don't require DDL migrations.

**Route blueprints** (`app/routes/`):
- `tables.py` — CRUD for tables and schema evolution (`PATCH /tables/{id}/schema` adds/removes columns). Enforces 500-column limit, unique column names, valid types (`string`, `number`, `boolean`).
- `rows.py` — CRUD for rows with type validation against the table's column schema. Filtering is done in-memory after fetching from SQLite. Pagination via `page`/`page_size` query params.

**Key helpers in routes:** `_get_column_map()` builds {name: type} dict for validation. `_validate_row_data()` type-checks values (strict: booleans are not numbers). `_coerce_filter_value()` converts query string filter values to the column's type.

**Data flow for row insert:** Request JSON → validate columns exist → type-check each value → store as JSON string in `rows.data` → return row with UUID.

## Test Setup

Tests use a temporary SQLite database via pytest fixtures in `tests/conftest.py`. The `client` fixture provides a Flask test client; `sample_table` creates a table with three columns (name/string, age/number, active/boolean) for row tests.
