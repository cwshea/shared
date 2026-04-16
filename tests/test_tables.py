def test_create_table(client):
    resp = client.post("/tables", json={
        "name": "customers",
        "columns": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "number"},
        ],
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "customers"
    assert len(data["columns"]) == 2
    assert data["id"]
    assert data["created_at"]


def test_create_table_missing_name(client):
    resp = client.post("/tables", json={"columns": [{"name": "x", "type": "string"}]})
    assert resp.status_code == 400


def test_create_table_no_columns(client):
    resp = client.post("/tables", json={"name": "t", "columns": []})
    assert resp.status_code == 400


def test_create_table_invalid_type(client):
    resp = client.post("/tables", json={
        "name": "t",
        "columns": [{"name": "x", "type": "date"}],
    })
    assert resp.status_code == 400
    assert "date" in resp.get_json()["error"]


def test_create_table_duplicate_columns(client):
    resp = client.post("/tables", json={
        "name": "t",
        "columns": [
            {"name": "x", "type": "string"},
            {"name": "x", "type": "number"},
        ],
    })
    assert resp.status_code == 400
    assert "Duplicate" in resp.get_json()["error"]


def test_get_table(client, sample_table):
    table_id = sample_table["id"]
    resp = client.get(f"/tables/{table_id}")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "customers"


def test_get_table_not_found(client):
    resp = client.get("/tables/nonexistent")
    assert resp.status_code == 404


def test_delete_table(client, sample_table):
    table_id = sample_table["id"]
    resp = client.delete(f"/tables/{table_id}")
    assert resp.status_code == 204

    resp = client.get(f"/tables/{table_id}")
    assert resp.status_code == 404


def test_delete_table_not_found(client):
    resp = client.delete("/tables/nonexistent")
    assert resp.status_code == 404


def test_update_schema_add_column(client, sample_table):
    table_id = sample_table["id"]
    resp = client.patch(f"/tables/{table_id}/schema", json={
        "add_columns": [{"name": "email", "type": "string"}],
    })
    assert resp.status_code == 200
    columns = [c["name"] for c in resp.get_json()["columns"]]
    assert "email" in columns


def test_update_schema_remove_column(client, sample_table):
    table_id = sample_table["id"]

    # Insert a row first so we can verify data migration
    client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "age": 30, "active": True},
    })

    resp = client.patch(f"/tables/{table_id}/schema", json={
        "remove_columns": ["age"],
    })
    assert resp.status_code == 200
    columns = [c["name"] for c in resp.get_json()["columns"]]
    assert "age" not in columns

    # Verify row data was cleaned up
    rows_resp = client.get(f"/tables/{table_id}/rows")
    row_data = rows_resp.get_json()["rows"][0]["data"]
    assert "age" not in row_data


def test_update_schema_add_duplicate_column(client, sample_table):
    table_id = sample_table["id"]
    resp = client.patch(f"/tables/{table_id}/schema", json={
        "add_columns": [{"name": "name", "type": "string"}],
    })
    assert resp.status_code == 400


def test_update_schema_remove_nonexistent(client, sample_table):
    table_id = sample_table["id"]
    resp = client.patch(f"/tables/{table_id}/schema", json={
        "remove_columns": ["nonexistent"],
    })
    assert resp.status_code == 400


def test_update_schema_empty_request(client, sample_table):
    table_id = sample_table["id"]
    resp = client.patch(f"/tables/{table_id}/schema", json={})
    assert resp.status_code == 400


def test_create_table_max_columns_exceeded(client):
    """Constraint: Maximum 500 columns per table."""
    columns = [{"name": f"col{i}", "type": "string"} for i in range(501)]
    resp = client.post("/tables", json={"name": "big", "columns": columns})
    assert resp.status_code == 400
    assert "500" in resp.get_json()["error"]


def test_create_table_exactly_max_columns(client):
    """500 columns should be allowed."""
    columns = [{"name": f"col{i}", "type": "string"} for i in range(500)]
    resp = client.post("/tables", json={"name": "big", "columns": columns})
    assert resp.status_code == 201
    assert len(resp.get_json()["columns"]) == 500


def test_update_schema_add_and_remove(client, sample_table):
    """Add and remove columns in the same request."""
    table_id = sample_table["id"]
    resp = client.patch(f"/tables/{table_id}/schema", json={
        "add_columns": [{"name": "email", "type": "string"}],
        "remove_columns": ["age"],
    })
    assert resp.status_code == 200
    col_names = [c["name"] for c in resp.get_json()["columns"]]
    assert "email" in col_names
    assert "age" not in col_names
    assert "name" in col_names
    assert "active" in col_names


def test_update_schema_not_found(client):
    """PATCH schema on non-existent table returns 404."""
    resp = client.patch("/tables/nonexistent/schema", json={
        "add_columns": [{"name": "x", "type": "string"}],
    })
    assert resp.status_code == 404


def test_update_schema_exceeds_max_columns(client, sample_table):
    """Adding columns that would exceed the 500 limit."""
    table_id = sample_table["id"]
    # sample_table has 3 columns, adding 498 would bring to 501
    new_cols = [{"name": f"col{i}", "type": "string"} for i in range(498)]
    resp = client.patch(f"/tables/{table_id}/schema", json={
        "add_columns": new_cols,
    })
    assert resp.status_code == 400
    assert "500" in resp.get_json()["error"]


def test_delete_table_cascades_rows(client, sample_table):
    """Deleting a table also deletes all its rows."""
    table_id = sample_table["id"]

    # Insert some rows
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob", "age": 25, "active": False}})

    # Verify rows exist
    resp = client.get(f"/tables/{table_id}/rows")
    assert resp.get_json()["total"] == 2

    # Delete table
    resp = client.delete(f"/tables/{table_id}")
    assert resp.status_code == 204

    # Verify table and rows are gone
    resp = client.get(f"/tables/{table_id}")
    assert resp.status_code == 404
    resp = client.get(f"/tables/{table_id}/rows")
    assert resp.status_code == 404


def test_create_table_non_json_body(client):
    """Sending non-JSON content type returns 400."""
    resp = client.post("/tables", data="not json", content_type="text/plain")
    assert resp.status_code == 400


def test_create_table_array_body(client):
    """Sending a JSON array instead of object returns 400."""
    resp = client.post("/tables", json=[{"name": "x"}])
    assert resp.status_code == 400
    assert "JSON object" in resp.get_json()["error"]


def test_update_schema_non_json_body(client, sample_table):
    """PATCH schema with non-JSON body returns 400."""
    table_id = sample_table["id"]
    resp = client.patch(f"/tables/{table_id}/schema", data="bad", content_type="text/plain")
    assert resp.status_code == 400


def test_update_schema_array_body(client, sample_table):
    """PATCH schema with JSON array instead of object returns 400."""
    table_id = sample_table["id"]
    resp = client.patch(f"/tables/{table_id}/schema", json=[{"name": "x"}])
    assert resp.status_code == 400
