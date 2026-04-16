curl -X POST http://localhost:3000/tables \
    -H "Content-Type: application/json" \
    -d '{"name":"customers","columns":[{"name":"name","type":"string"},{"name":"age","type":"number"}]}'
