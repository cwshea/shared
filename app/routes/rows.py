import json
import re
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.database import get_db

bp = Blueprint("rows", __name__)

FILTER_PATTERN = re.compile(r"^filter\[(.+)]$")


@bp.post("/tables/<table_id>/rows")
def insert_row(table_id):
    db = get_db()

    table = db.execute("SELECT id FROM tables WHERE id = ?", (table_id,)).fetchone()
    if not table:
        return jsonify(error="Table not found"), 404

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    data = body.get("data")
    if not isinstance(data, dict):
        return jsonify(error="data must be an object"), 400

    column_map = _get_column_map(db, table_id)
    error = _validate_row_data(data, column_map)
    if error:
        return jsonify(error=error), 400

    row_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        "INSERT INTO rows (id, table_id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (row_id, table_id, json.dumps(data), now, now),
    )
    db.commit()

    row = db.execute("SELECT * FROM rows WHERE id = ?", (row_id,)).fetchone()
    return jsonify(_row_response(row)), 201


@bp.get("/tables/<table_id>/rows")
def get_rows(table_id):
    db = get_db()

    table = db.execute("SELECT id FROM tables WHERE id = ?", (table_id,)).fetchone()
    if not table:
        return jsonify(error="Table not found"), 404

    column_map = _get_column_map(db, table_id)

    # Pagination
    page = max(1, request.args.get("page", 1, type=int))
    page_size = min(1000, max(1, request.args.get("page_size", 50, type=int)))

    # Parse filter[column]=value query params
    filters = {}
    for key in request.args:
        match = FILTER_PATTERN.match(key)
        if match:
            col_name = match.group(1)
            if col_name not in column_map:
                return jsonify(error=f"Unknown filter column '{col_name}'"), 400
            filters[col_name] = _coerce_filter_value(
                request.args[key], column_map[col_name]
            )

    # Fetch rows
    all_rows = db.execute(
        "SELECT * FROM rows WHERE table_id = ? ORDER BY created_at",
        (table_id,),
    ).fetchall()

    # Apply filters in memory (data is stored as JSON)
    if filters:
        filtered = []
        for row in all_rows:
            data = json.loads(row["data"])
            if all(data.get(k) == v for k, v in filters.items()):
                filtered.append(row)
        all_rows = filtered

    total = len(all_rows)
    start = (page - 1) * page_size
    page_rows = all_rows[start : start + page_size]

    return jsonify(
        rows=[_row_response(r) for r in page_rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@bp.put("/tables/<table_id>/rows/<row_id>")
def update_row(table_id, row_id):
    db = get_db()

    table = db.execute("SELECT id FROM tables WHERE id = ?", (table_id,)).fetchone()
    if not table:
        return jsonify(error="Table not found"), 404

    row = db.execute(
        "SELECT * FROM rows WHERE id = ? AND table_id = ?", (row_id, table_id)
    ).fetchone()
    if not row:
        return jsonify(error="Row not found"), 404

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    data = body.get("data")
    if not isinstance(data, dict):
        return jsonify(error="data must be an object"), 400

    column_map = _get_column_map(db, table_id)
    error = _validate_row_data(data, column_map)
    if error:
        return jsonify(error=error), 400

    existing_data = json.loads(row["data"])
    existing_data.update(data)
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        "UPDATE rows SET data = ?, updated_at = ? WHERE id = ?",
        (json.dumps(existing_data), now, row_id),
    )
    db.commit()

    updated = db.execute("SELECT * FROM rows WHERE id = ?", (row_id,)).fetchone()
    return jsonify(_row_response(updated))


@bp.delete("/tables/<table_id>/rows/<row_id>")
def delete_row(table_id, row_id):
    db = get_db()

    table = db.execute("SELECT id FROM tables WHERE id = ?", (table_id,)).fetchone()
    if not table:
        return jsonify(error="Table not found"), 404

    row = db.execute(
        "SELECT id FROM rows WHERE id = ? AND table_id = ?", (row_id, table_id)
    ).fetchone()
    if not row:
        return jsonify(error="Row not found"), 404

    db.execute("DELETE FROM rows WHERE id = ?", (row_id,))
    db.commit()
    return "", 204


def _get_column_map(db, table_id):
    columns = db.execute(
        "SELECT name, type FROM columns WHERE table_id = ?", (table_id,)
    ).fetchall()
    return {c["name"]: c["type"] for c in columns}


def _validate_row_data(data, column_map):
    for key, value in data.items():
        if key not in column_map:
            return f"Unknown column '{key}'. Valid columns: {', '.join(sorted(column_map.keys()))}"

        if value is None:
            continue

        col_type = column_map[key]
        if col_type == "string" and not isinstance(value, str):
            return f"Column '{key}' expects a string, got {type(value).__name__}"
        if col_type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            return f"Column '{key}' expects a number, got {type(value).__name__}"
        if col_type == "boolean" and not isinstance(value, bool):
            return f"Column '{key}' expects a boolean, got {type(value).__name__}"

    return None


def _coerce_filter_value(value, col_type):
    if col_type == "number":
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return value
    if col_type == "boolean":
        if value.lower() in ("true", "1"):
            return True
        if value.lower() in ("false", "0"):
            return False
    return value


def _row_response(row):
    return {
        "id": row["id"],
        "data": json.loads(row["data"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
