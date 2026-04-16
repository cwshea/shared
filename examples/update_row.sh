#!/usr/bin/env bash
# Usage: ./update_row.sh <table_id> <row_id>

TABLE_ID=${1:?Usage: ./update_row.sh <table_id> <row_id>}
ROW_ID=${2:?Usage: ./update_row.sh <table_id> <row_id>}

curl -s -X PUT "http://localhost:3000/tables/$TABLE_ID/rows/$ROW_ID" \
    -H "Content-Type: application/json" \
    -d '{"data":{"name":"Alice Updated","age":31}}' | python3 -m json.tool
