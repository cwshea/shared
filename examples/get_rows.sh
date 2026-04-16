#!/usr/bin/env bash
# Usage: ./get_rows.sh <table_id>

TABLE_ID=${1:?Usage: ./get_rows.sh <table_id>}

curl -s "http://localhost:3000/tables/$TABLE_ID/rows" | python3 -m json.tool
