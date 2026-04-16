#!/usr/bin/env bash
# Usage: ./delete_row.sh <table_id> <row_id>

TABLE_ID=${1:?Usage: ./delete_row.sh <table_id> <row_id>}
ROW_ID=${2:?Usage: ./delete_row.sh <table_id> <row_id>}

curl -s -X DELETE "http://localhost:3000/tables/$TABLE_ID/rows/$ROW_ID" \
    -w "\nHTTP %{http_code}\n"
