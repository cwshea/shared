#!/usr/bin/env bash
# Usage: ./update_schema.sh <table_id>
# Adds an "email" column and removes the "age" column.

TABLE_ID=${1:?Usage: ./update_schema.sh <table_id>}

curl -s -X PATCH "http://localhost:3000/tables/$TABLE_ID/schema" \
    -H "Content-Type: application/json" \
    -d '{"add_columns":[{"name":"email","type":"string"}],"remove_columns":["age"]}' | python3 -m json.tool
