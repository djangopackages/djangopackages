#!/bin/sh
set -e

# Check if the Q cluster is alive
output=$(uv run -m manage qinfo --skip-checks 2>&1) || {
    echo "Failed to run qinfo:"
    echo "$output"
    exit 1
}

echo "$output" | grep -q "Workers" && exit 0

echo "Django-Q2 cluster not running"
echo "$output"
exit 1
