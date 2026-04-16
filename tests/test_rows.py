def test_insert_row(client, sample_table):
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "age": 30, "active": True},
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["data"]["name"] == "Alice"
    assert data["data"]["age"] == 30
    assert data["data"]["active"] is True
    assert data["id"]


def test_insert_row_partial_data(client, sample_table):
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Bob"},
    })
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "Bob"


def test_insert_row_unknown_column(client, sample_table):
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "unknown": "value"},
    })
    assert resp.status_code == 400
    assert "Unknown column" in resp.get_json()["error"]


def test_insert_row_wrong_type(client, sample_table):
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "age": "thirty"},
    })
    assert resp.status_code == 400
    assert "expects a number" in resp.get_json()["error"]


def test_insert_row_boolean_type_check(client, sample_table):
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"active": "yes"},
    })
    assert resp.status_code == 400
    assert "expects a boolean" in resp.get_json()["error"]


def test_insert_row_table_not_found(client):
    resp = client.post("/tables/nonexistent/rows", json={"data": {}})
    assert resp.status_code == 404


def test_get_rows(client, sample_table):
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob", "age": 25, "active": False}})

    resp = client.get(f"/tables/{table_id}/rows")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 2
    assert len(data["rows"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 50


def test_get_rows_pagination(client, sample_table):
    table_id = sample_table["id"]
    for i in range(5):
        client.post(f"/tables/{table_id}/rows", json={"data": {"name": f"user{i}", "age": i, "active": True}})

    resp = client.get(f"/tables/{table_id}/rows?page=1&page_size=2")
    data = resp.get_json()
    assert data["total"] == 5
    assert len(data["rows"]) == 2
    assert data["page"] == 1

    resp2 = client.get(f"/tables/{table_id}/rows?page=3&page_size=2")
    data2 = resp2.get_json()
    assert len(data2["rows"]) == 1


def test_get_rows_filter(client, sample_table):
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob", "age": 25, "active": False}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Charlie", "age": 30, "active": True}})

    resp = client.get(f"/tables/{table_id}/rows?filter[age]=30")
    data = resp.get_json()
    assert data["total"] == 2
    names = {r["data"]["name"] for r in data["rows"]}
    assert names == {"Alice", "Charlie"}


def test_get_rows_filter_boolean(client, sample_table):
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "active": True}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob", "active": False}})

    resp = client.get(f"/tables/{table_id}/rows?filter[active]=true")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["data"]["name"] == "Alice"


def test_get_rows_filter_string(client, sample_table):
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice"}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob"}})

    resp = client.get(f"/tables/{table_id}/rows?filter[name]=Alice")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["data"]["name"] == "Alice"


def test_get_rows_filter_multiple(client, sample_table):
    """Filter on multiple columns at once."""
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob", "age": 30, "active": False}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Charlie", "age": 25, "active": True}})

    resp = client.get(f"/tables/{table_id}/rows?filter[age]=30&filter[active]=true")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["data"]["name"] == "Alice"


def test_get_rows_filter_no_match(client, sample_table):
    """Filter returns empty list when no rows match."""
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "age": 30}})

    resp = client.get(f"/tables/{table_id}/rows?filter[name]=Nobody")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["total"] == 0
    assert data["rows"] == []


def test_get_rows_filter_boolean_false(client, sample_table):
    """Filter on boolean false value."""
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "active": True}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob", "active": False}})

    resp = client.get(f"/tables/{table_id}/rows?filter[active]=false")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["data"]["name"] == "Bob"


def test_get_rows_filter_number_float(client, sample_table):
    """Filter on a float number value."""
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "age": 30.5}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob", "age": 25}})

    resp = client.get(f"/tables/{table_id}/rows?filter[age]=30.5")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["data"]["name"] == "Alice"


def test_get_rows_filter_with_pagination(client, sample_table):
    """Filtering is applied before pagination."""
    table_id = sample_table["id"]
    for i in range(5):
        client.post(f"/tables/{table_id}/rows", json={"data": {"name": f"user{i}", "age": 30, "active": True}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "other", "age": 25, "active": False}})

    resp = client.get(f"/tables/{table_id}/rows?filter[age]=30&page=1&page_size=3")
    data = resp.get_json()
    assert data["total"] == 5  # 5 match the filter
    assert len(data["rows"]) == 3  # but only 3 per page

    resp2 = client.get(f"/tables/{table_id}/rows?filter[age]=30&page=2&page_size=3")
    data2 = resp2.get_json()
    assert data2["total"] == 5
    assert len(data2["rows"]) == 2  # remaining 2 on page 2


def test_get_rows_filter_missing_column_in_row(client, sample_table):
    """Rows that don't have the filtered column should not match."""
    table_id = sample_table["id"]
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Alice", "age": 30}})
    client.post(f"/tables/{table_id}/rows", json={"data": {"name": "Bob"}})  # no age

    resp = client.get(f"/tables/{table_id}/rows?filter[age]=30")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["data"]["name"] == "Alice"


def test_get_rows_filter_unknown_column(client, sample_table):
    table_id = sample_table["id"]
    resp = client.get(f"/tables/{table_id}/rows?filter[unknown]=x")
    assert resp.status_code == 400


def test_update_row(client, sample_table):
    table_id = sample_table["id"]
    create_resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "age": 30, "active": True},
    })
    row_id = create_resp.get_json()["id"]

    resp = client.put(f"/tables/{table_id}/rows/{row_id}", json={
        "data": {"age": 31},
    })
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["name"] == "Alice"  # unchanged
    assert data["age"] == 31  # updated
    assert data["active"] is True  # unchanged


def test_update_row_not_found(client, sample_table):
    table_id = sample_table["id"]
    resp = client.put(f"/tables/{table_id}/rows/nonexistent", json={"data": {"name": "x"}})
    assert resp.status_code == 404


def test_delete_row(client, sample_table):
    table_id = sample_table["id"]
    create_resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "age": 30, "active": True},
    })
    row_id = create_resp.get_json()["id"]

    resp = client.delete(f"/tables/{table_id}/rows/{row_id}")
    assert resp.status_code == 204

    # Verify it's gone
    rows_resp = client.get(f"/tables/{table_id}/rows")
    assert rows_resp.get_json()["total"] == 0


def test_delete_row_not_found(client, sample_table):
    table_id = sample_table["id"]
    resp = client.delete(f"/tables/{table_id}/rows/nonexistent")
    assert resp.status_code == 404


def test_insert_row_number_rejects_boolean(client, sample_table):
    """Number column rejects boolean values (bool is subclass of int in Python)."""
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"age": True},
    })
    assert resp.status_code == 400
    assert "expects a number" in resp.get_json()["error"]


def test_insert_row_non_json_body(client, sample_table):
    """Sending non-JSON content type returns 400."""
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", data="not json", content_type="text/plain")
    assert resp.status_code == 400


def test_insert_row_array_body(client, sample_table):
    """Sending a JSON array instead of object returns 400."""
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json=[{"name": "Alice"}])
    assert resp.status_code == 400
    assert "JSON object" in resp.get_json()["error"]


def test_update_row_unknown_column(client, sample_table):
    """PUT row with unknown column returns 400."""
    table_id = sample_table["id"]
    create_resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice"},
    })
    row_id = create_resp.get_json()["id"]

    resp = client.put(f"/tables/{table_id}/rows/{row_id}", json={
        "data": {"nonexistent": "value"},
    })
    assert resp.status_code == 400
    assert "Unknown column" in resp.get_json()["error"]


def test_update_row_non_json_body(client, sample_table):
    """PUT row with non-JSON body returns 400."""
    table_id = sample_table["id"]
    create_resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice"},
    })
    row_id = create_resp.get_json()["id"]

    resp = client.put(f"/tables/{table_id}/rows/{row_id}", data="bad", content_type="text/plain")
    assert resp.status_code == 400


def test_update_row_table_not_found(client):
    """PUT row on non-existent table returns 404."""
    resp = client.put("/tables/nonexistent/rows/fake-id", json={"data": {"x": 1}})
    assert resp.status_code == 404
    assert "Table not found" in resp.get_json()["error"]


def test_delete_row_table_not_found(client):
    """DELETE row on non-existent table returns 404."""
    resp = client.delete("/tables/nonexistent/rows/fake-id")
    assert resp.status_code == 404
    assert "Table not found" in resp.get_json()["error"]


def test_insert_row_number_float(client, sample_table):
    """Number columns should accept both int and float."""
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"age": 30.5},
    })
    assert resp.status_code == 201
    assert resp.get_json()["data"]["age"] == 30.5


def test_insert_row_string_rejects_number(client, sample_table):
    """String column rejects non-string values."""
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": 123},
    })
    assert resp.status_code == 400
    assert "expects a string" in resp.get_json()["error"]


def test_insert_row_boolean_rejects_number(client, sample_table):
    """Boolean column rejects numeric values."""
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"active": 1},
    })
    assert resp.status_code == 400
    assert "expects a boolean" in resp.get_json()["error"]


def test_insert_row_null_value(client, sample_table):
    """Null values should be accepted for any column type."""
    table_id = sample_table["id"]
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": None, "age": None, "active": None},
    })
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["name"] is None
    assert data["age"] is None
    assert data["active"] is None


def test_get_rows_table_not_found(client):
    """GET rows on non-existent table returns 404."""
    resp = client.get("/tables/nonexistent/rows")
    assert resp.status_code == 404


def test_get_rows_empty_table(client, sample_table):
    """GET rows on a table with no rows returns empty list."""
    table_id = sample_table["id"]
    resp = client.get(f"/tables/{table_id}/rows")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["rows"] == []


def test_update_row_invalid_type(client, sample_table):
    """PUT row with wrong type returns 400."""
    table_id = sample_table["id"]
    create_resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "age": 30, "active": True},
    })
    row_id = create_resp.get_json()["id"]

    resp = client.put(f"/tables/{table_id}/rows/{row_id}", json={
        "data": {"age": "not a number"},
    })
    assert resp.status_code == 400
    assert "expects a number" in resp.get_json()["error"]


def test_full_workflow(client):
    """Test the example flow from the spec."""
    # 1. Create table
    resp = client.post("/tables", json={
        "name": "customers",
        "columns": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "number"},
            {"name": "active", "type": "boolean"},
        ],
    })
    assert resp.status_code == 201
    table_id = resp.get_json()["id"]

    # 2. Insert row
    resp = client.post(f"/tables/{table_id}/rows", json={
        "data": {"name": "Alice", "age": 30, "active": True},
    })
    assert resp.status_code == 201
    row_id = resp.get_json()["id"]

    # 3. Query all rows
    resp = client.get(f"/tables/{table_id}/rows")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 1

    # 4. Add new column "email"
    resp = client.patch(f"/tables/{table_id}/schema", json={
        "add_columns": [{"name": "email", "type": "string"}],
    })
    assert resp.status_code == 200
    col_names = [c["name"] for c in resp.get_json()["columns"]]
    assert "email" in col_names

    # 5. Update existing row with email
    resp = client.put(f"/tables/{table_id}/rows/{row_id}", json={
        "data": {"email": "alice@example.com"},
    })
    assert resp.status_code == 200
    assert resp.get_json()["data"]["email"] == "alice@example.com"
    assert resp.get_json()["data"]["name"] == "Alice"  # unchanged
