#!/usr/bin/env bash
# Usage: ./filter_rows.sh <table_id> <column> <value>
# Example: ./filter_rows.sh abc123 name Alice

TABLE_ID=${1:?Usage: ./filter_rows.sh <table_id> <column> <value>}
COLUMN=${2:?Usage: ./filter_rows.sh <table_id> <column> <value>}
VALUE=${3:?Usage: ./filter_rows.sh <table_id> <column> <value>}

curl -s "http://localhost:3000/tables/$TABLE_ID/rows?filter[$COLUMN]=$VALUE" | python3 -m json.tool
