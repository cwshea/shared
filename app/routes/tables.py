import json
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.database import get_db

bp = Blueprint("tables", __name__)

VALID_TYPES = {"string", "number", "boolean"}
MAX_COLUMNS = 500


@bp.post("/tables")
def create_table():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    name = body.get("name")
    columns = body.get("columns")

    if not name or not isinstance(name, str) or not name.strip():
        return jsonify(error="Table name is required"), 400

    if not isinstance(columns, list) or len(columns) == 0:
        return jsonify(error="At least one column is required"), 400

    if len(columns) > MAX_COLUMNS:
        return jsonify(error=f"Maximum {MAX_COLUMNS} columns allowed"), 400

    # Validate columns
    col_names = set()
    for col in columns:
        col_name = col.get("name")
        col_type = col.get("type")

        if not col_name or not isinstance(col_name, str) or not col_name.strip():
            return jsonify(error="Column name is required"), 400

        if col_type not in VALID_TYPES:
            return jsonify(error=f"Invalid column type '{col_type}'. Must be one of: boolean, number, string"), 400

        if col_name in col_names:
            return jsonify(error=f"Duplicate column name '{col_name}'"), 400

        col_names.add(col_name)

    db = get_db()
    table_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        "INSERT INTO tables (id, name, created_at) VALUES (?, ?, ?)",
        (table_id, name.strip(), now),
    )

    for i, col in enumerate(columns):
        db.execute(
            "INSERT INTO columns (id, table_id, name, type, position) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), table_id, col["name"].strip(), col["type"], i),
        )

    db.commit()

    return jsonify(get_table_response(db, table_id)), 201


@bp.get("/tables/<table_id>")
def get_table(table_id):
    db = get_db()
    table = get_table_response(db, table_id)
    if not table:
        return jsonify(error="Table not found"), 404
    return jsonify(table)


@bp.delete("/tables/<table_id>")
def delete_table(table_id):
    db = get_db()
    row = db.execute("SELECT id FROM tables WHERE id = ?", (table_id,)).fetchone()
    if not row:
        return jsonify(error="Table not found"), 404

    db.execute("DELETE FROM tables WHERE id = ?", (table_id,))
    db.commit()
    return "", 204


@bp.patch("/tables/<table_id>/schema")
def update_schema(table_id):
    db = get_db()

    table = db.execute("SELECT id FROM tables WHERE id = ?", (table_id,)).fetchone()
    if not table:
        return jsonify(error="Table not found"), 404

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    add_columns = body.get("add_columns")
    remove_columns = body.get("remove_columns")

    if not add_columns and not remove_columns:
        return jsonify(error="Must specify add_columns or remove_columns"), 400

    existing = db.execute(
        "SELECT name, position FROM columns WHERE table_id = ?", (table_id,)
    ).fetchall()
    existing_names = {c["name"] for c in existing}
    max_position = max((c["position"] for c in existing), default=-1)

    # Validate remove_columns
    names_to_remove = set()
    if remove_columns:
        if not isinstance(remove_columns, list):
            return jsonify(error="remove_columns must be an array"), 400
        for col_name in remove_columns:
            if col_name not in existing_names:
                return jsonify(error=f"Column '{col_name}' does not exist"), 400
            names_to_remove.add(col_name)

    # Validate add_columns
    if add_columns:
        if not isinstance(add_columns, list):
            return jsonify(error="add_columns must be an array"), 400

        add_names = set()
        for col in add_columns:
            col_name = col.get("name")
            col_type = col.get("type")

            if not col_name or not isinstance(col_name, str) or not col_name.strip():
                return jsonify(error="Column name is required"), 400

            if col_type not in VALID_TYPES:
                return jsonify(error=f"Invalid column type '{col_type}'. Must be one of: boolean, number, string"), 400

            if col_name in existing_names and col_name not in names_to_remove:
                return jsonify(error=f"Column '{col_name}' already exists"), 400

            if col_name in add_names:
                return jsonify(error=f"Duplicate column name '{col_name}'"), 400

            add_names.add(col_name)

        new_total = len(existing_names) - len(names_to_remove) + len(add_columns)
        if new_total > MAX_COLUMNS:
            return jsonify(error=f"Would exceed maximum of {MAX_COLUMNS} columns"), 400

    # Remove columns
    if names_to_remove:
        for col_name in names_to_remove:
            db.execute(
                "DELETE FROM columns WHERE table_id = ? AND name = ?",
                (table_id, col_name),
            )

        # Clean up row data
        rows = db.execute(
            "SELECT id, data FROM rows WHERE table_id = ?", (table_id,)
        ).fetchall()
        for row in rows:
            data = json.loads(row["data"])
            for col_name in names_to_remove:
                data.pop(col_name, None)
            db.execute(
                "UPDATE rows SET data = ? WHERE id = ?",
                (json.dumps(data), row["id"]),
            )

    # Add columns
    if add_columns:
        for i, col in enumerate(add_columns):
            db.execute(
                "INSERT INTO columns (id, table_id, name, type, position) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), table_id, col["name"].strip(), col["type"], max_position + 1 + i),
            )

    db.commit()

    return jsonify(get_table_response(db, table_id))


def get_table_response(db, table_id):
    table = db.execute("SELECT * FROM tables WHERE id = ?", (table_id,)).fetchone()
    if not table:
        return None

    columns = db.execute(
        "SELECT name, type FROM columns WHERE table_id = ? ORDER BY position",
        (table_id,),
    ).fetchall()

    return {
        "id": table["id"],
        "name": table["name"],
        "columns": [{"name": c["name"], "type": c["type"]} for c in columns],
        "created_at": table["created_at"],
    }
