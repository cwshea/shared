#!/usr/bin/env bash
# Usage: ./get_tables.sh <table_id>

TABLE_ID=${1:?Usage: ./get_tables.sh <table_id>}

curl -s -X GET "http://localhost:3000/tables/$TABLE_ID" | python3 -m json.tool
