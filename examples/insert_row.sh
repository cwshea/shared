#!/usr/bin/env bash
# Usage: ./insert_row.sh <table_id>

TABLE_ID=${1:?Usage: ./insert_row.sh <table_id>}

curl -s -X POST "http://localhost:3000/tables/$TABLE_ID/rows" \
    -H "Content-Type: application/json" \
    -d '{"data":{"name":"Alice","age":30}}' | python3 -m json.tool
