# Data Tables API

A lightweight REST API for a flexible "data table" system — create tables with custom schemas, store and retrieve data, and modify schemas on the fly. Built with Flask and SQLite.

## Setup

### Quick Start (Docker + Colima)

```bash
./startup.sh
```

This will start Colima if needed, build the container, and launch the API at `http://localhost:3000`.

To stop: `docker compose down` (or `docker-compose down`)

### Local (Python)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

The API will be running at `http://localhost:3000`.

### Run Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

55 tests covering all endpoints, validation, error handling, and the full example workflow.

A VS Code `launch.json` is included for debugging tests with breakpoints.

---

## API Documentation

### Health Check

```
GET /health
```

Response: `{"status": "ok"}`

---

### 1. Create Table

```
POST /tables
```

**Request body:**

```json
{
  "name": "customers",
  "columns": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "number"},
    {"name": "active", "type": "boolean"}
  ]
}
```

**Response (201):**

```json
{
  "id": "uuid",
  "name": "customers",
  "columns": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "number"},
    {"name": "active", "type": "boolean"}
  ],
  "created_at": "2026-04-13T..."
}
```

Supported column types: `string`, `number`, `boolean`.

**Errors:**

| Status | Condition |
|--------|-----------|
| 400 | Missing or empty table name |
| 400 | No columns provided |
| 400 | More than 500 columns |
| 400 | Invalid column type |
| 400 | Duplicate column names |
| 400 | Request body is not a JSON object |

---

### 2. Get Table

```
GET /tables/{table_id}
```

**Response (200):** Same shape as create response.

**Errors:**

| Status | Condition |
|--------|-----------|
| 404 | Table not found |

---

### 3. Delete Table

```
DELETE /tables/{table_id}
```

**Response:** `204 No Content`

Cascade-deletes all rows and columns.

**Errors:**

| Status | Condition |
|--------|-----------|
| 404 | Table not found |

---

### 4. Update Schema

```
PATCH /tables/{table_id}/schema
```

**Request body:**

```json
{
  "add_columns": [{"name": "email", "type": "string"}],
  "remove_columns": ["age"]
}
```

Both fields are optional, but at least one must be provided. Removing a column also strips that key from all existing row data.

**Response (200):** Updated table with new column list.

**Errors:**

| Status | Condition |
|--------|-----------|
| 400 | Neither `add_columns` nor `remove_columns` provided |
| 400 | Column to remove does not exist |
| 400 | Column to add already exists |
| 400 | Duplicate column name in `add_columns` |
| 400 | Invalid column type |
| 400 | Would exceed 500 column limit |
| 400 | Request body is not a JSON object |
| 404 | Table not found |

---

### 5. Insert Row

```
POST /tables/{table_id}/rows
```

**Request body:**

```json
{
  "data": {"name": "Alice", "age": 30, "active": true}
}
```

Values are type-checked against the column definitions. Not all columns are required. Null values are accepted for any column type.

**Response (201):**

```json
{
  "id": "uuid",
  "data": {"name": "Alice", "age": 30, "active": true},
  "created_at": "...",
  "updated_at": "..."
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| 400 | `data` is missing or not an object |
| 400 | Unknown column name |
| 400 | Type mismatch (e.g. string value for a number column) |
| 400 | Request body is not a JSON object |
| 404 | Table not found |

---

### 6. Get Rows

```
GET /tables/{table_id}/rows
```

**Query parameters:**

| Param | Default | Description |
|-------|---------|-------------|
| `page` | 1 | Page number |
| `page_size` | 50 | Rows per page (max 1000) |
| `filter[column]` | — | Filter by column value (e.g. `?filter[name]=Alice&filter[age]=30`) |

Filter values are automatically coerced to the column's type (numbers parsed from strings, `"true"`/`"false"` parsed to booleans).

**Response (200):**

```json
{
  "rows": [...],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| 400 | Unknown filter column |
| 404 | Table not found |

---

### 7. Update Row

```
PUT /tables/{table_id}/rows/{row_id}
```

**Request body:**

```json
{
  "data": {"age": 31}
}
```

Merges with existing data (partial update). Values are type-checked.

**Response (200):** Updated row.

**Errors:**

| Status | Condition |
|--------|-----------|
| 400 | `data` is missing or not an object |
| 400 | Unknown column name |
| 400 | Type mismatch |
| 400 | Request body is not a JSON object |
| 404 | Table not found |
| 404 | Row not found |

---

### 8. Delete Row

```
DELETE /tables/{table_id}/rows/{row_id}
```

**Response:** `204 No Content`

**Errors:**

| Status | Condition |
|--------|-----------|
| 404 | Table not found |
| 404 | Row not found |

---

## Example Scripts

Shell scripts for exercising each endpoint are in the `examples/` directory:

| Script | Endpoint | Usage |
|--------|----------|-------|
| `create_table.sh` | `POST /tables` | `./examples/create_table.sh` |
| `get_tables.sh` | `GET /tables/{id}` | `./examples/get_tables.sh` |
| `delete_table.sh` | `DELETE /tables/{id}` | `./examples/delete_table.sh <table_id>` |
| `update_schema.sh` | `PATCH /tables/{id}/schema` | `./examples/update_schema.sh <table_id>` |
| `insert_row.sh` | `POST /tables/{id}/rows` | `./examples/insert_row.sh <table_id>` |
| `get_rows.sh` | `GET /tables/{id}/rows` | `./examples/get_rows.sh <table_id>` |
| `filter_rows.sh` | `GET /tables/{id}/rows?filter` | `./examples/filter_rows.sh <table_id> <column> <value>` |
| `update_row.sh` | `PUT /tables/{id}/rows/{id}` | `./examples/update_row.sh <table_id> <row_id>` |
| `delete_row.sh` | `DELETE /tables/{id}/rows/{id}` | `./examples/delete_row.sh <table_id> <row_id>` |

### Full Workflow with curl

```bash
BASE=http://localhost:3000

# 1. Create a "customers" table
TABLE=$(curl -s -X POST $BASE/tables \
  -H "Content-Type: application/json" \
  -d '{"name":"customers","columns":[{"name":"name","type":"string"},{"name":"age","type":"number"},{"name":"active","type":"boolean"}]}')

echo "$TABLE" | python3 -m json.tool
TABLE_ID=$(echo "$TABLE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 2. Insert rows
ROW=$(curl -s -X POST $BASE/tables/$TABLE_ID/rows \
  -H "Content-Type: application/json" \
  -d '{"data":{"name":"Alice","age":30,"active":true}}')

echo "$ROW" | python3 -m json.tool
ROW_ID=$(echo "$ROW" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST $BASE/tables/$TABLE_ID/rows \
  -H "Content-Type: application/json" \
  -d '{"data":{"name":"Bob","age":25,"active":false}}' | python3 -m json.tool

# 3. Query all rows
curl -s "$BASE/tables/$TABLE_ID/rows" | python3 -m json.tool

# 4. Filter rows by age
curl -s "$BASE/tables/$TABLE_ID/rows?filter[age]=30" | python3 -m json.tool

# 5. Add a new "email" column
curl -s -X PATCH $BASE/tables/$TABLE_ID/schema \
  -H "Content-Type: application/json" \
  -d '{"add_columns":[{"name":"email","type":"string"}]}' | python3 -m json.tool

# 6. Update Alice's row with email
curl -s -X PUT $BASE/tables/$TABLE_ID/rows/$ROW_ID \
  -H "Content-Type: application/json" \
  -d '{"data":{"email":"alice@example.com"}}' | python3 -m json.tool

# 7. Delete Bob's row (get his ID first)
BOB_ID=$(curl -s "$BASE/tables/$TABLE_ID/rows?filter[name]=Bob" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['rows'][0]['id'])")
curl -s -X DELETE $BASE/tables/$TABLE_ID/rows/$BOB_ID -w "\nHTTP %{http_code}\n"

# 8. Delete the table
curl -s -X DELETE $BASE/tables/$TABLE_ID -w "\nHTTP %{http_code}\n"
```

---

## Design Decisions

### Storage: JSON-in-SQLite (Document-Relational Hybrid)

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│  tables   │──1:N──│ columns  │       │   rows   │
│           │       │          │       │          │
│ id (PK)   │       │ id (PK)  │       │ id (PK)  │
│ name      │       │ table_id │       │ table_id │
│ created_at│       │ name     │       │ data{}   │
│           │       │ type     │       │ created  │
└──────────┘       │ position │       │ updated  │
                    └──────────┘       └──────────┘
```

- **`tables`** — metadata about each user-defined table
- **`columns`** — schema definitions (name, type, ordering) per table
- **`rows`** — each row stores its data as a JSON string in the `data` column

**Why this approach:**

| Approach | Pros | Cons |
|----------|------|------|
| **JSON data column (chosen)** | Schema changes are instant (no DDL), simple row insert/update, flexible | Filtering requires parsing JSON in-memory; no per-column indexes |
| Dynamic DDL (CREATE TABLE per user table) | Native SQL queries, indexes per column | Schema changes require ALTER TABLE, naming collisions, complex migration |
| EAV (entity-attribute-value) | Fully normalized, flexible | Complex joins for every query, poor read performance |

The JSON approach is the best fit for this use case: schema changes are frequent and should be fast, the dataset sizes are moderate, and the API already returns full row objects rather than individual columns.

### Error Handling

All endpoints return consistent JSON error responses:

```json
{"error": "Description of what went wrong"}
```

Validation is applied at multiple levels:
- **Request format** — body must be a JSON object (not an array, string, etc.)
- **Schema validation** — column names must be non-empty strings, types must be `string`/`number`/`boolean`, names must be unique
- **Data validation** — row values are type-checked against their column definitions; booleans are not accepted as numbers
- **Referential integrity** — operations on non-existent tables or rows return 404

### Tradeoffs and Known Limitations

- **Filtering is in-memory** — rows are loaded from SQLite and filtered in Python. This is fine for moderate data sizes but would not scale to millions of rows per table. A production system would use SQLite's `json_extract()` or move to PostgreSQL with JSONB indexes.
- **No authentication/authorization** — any client can access any table.
- **No concurrent write protection** — SQLite with WAL mode handles concurrent reads well but serializes writes. Fine for moderate load.
- **Column ordering** — tracked via a `position` field; gaps may appear after removes but ordering is preserved.
- **Null handling** — columns are optional when inserting rows. Missing columns are simply absent from the JSON data (not stored as null).

### Why Flask + SQLite

- **Chosen for the execution environment** — this project runs on a laptop, so SQLite is ideal: no database server to install, configure, or keep running. It's embedded in Python's standard library and works out of the box.
- **Minimal footprint** — the entire API is ~300 lines of Python.
- **Easy to test** — Flask's test client provides fast, isolated in-process testing without starting a server.
- **Easy to extend** — the database layer is isolated in `app/database.py`, and all queries use standard SQL. To migrate to PostgreSQL, MySQL, or another SQL database, the main changes would be:
  1. Swap the `sqlite3` connection in `database.py` for the target database driver (e.g. `psycopg2` for PostgreSQL)
  2. Update the `PRAGMA` statements to the equivalent database settings
  3. Optionally replace in-memory JSON filtering with native JSON operators (e.g. PostgreSQL's `jsonb` operators) for better performance at scale
