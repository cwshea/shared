#!/usr/bin/env bash
set -e

# Start Colima if not already running
if ! colima status &>/dev/null; then
  echo "Starting Colima..."
  colima start
fi

# Detect docker compose command
if docker compose version &>/dev/null; then
  DC="docker compose"
elif command -v docker-compose &>/dev/null; then
  DC="docker-compose"
else
  echo "Error: neither 'docker compose' nor 'docker-compose' found."
  exit 1
fi

# Build and run
echo "Building and starting Data Tables API..."
$DC up --build -d

echo ""
echo "Data Tables API is running at http://localhost:3000"
echo "To view logs: $DC logs -f"
echo "To stop:      $DC down"
