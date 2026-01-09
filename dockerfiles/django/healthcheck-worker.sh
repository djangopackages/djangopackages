#!/bin/sh
set -e

# Check if the Q cluster is alive
uv run -m manage qinfo --skip-checks | grep -q "Workers" && exit 0

echo "Django-Q2 cluster not running"
exit 1
