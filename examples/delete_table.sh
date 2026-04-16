#!/usr/bin/env bash
# Usage: ./delete_table.sh <table_id>

TABLE_ID=${1:?Usage: ./delete_table.sh <table_id>}

curl -s -X DELETE "http://localhost:3000/tables/$TABLE_ID" \
    -w "\nHTTP %{http_code}\n"
