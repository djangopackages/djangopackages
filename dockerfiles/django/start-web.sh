#!/bin/sh
uv run -m manage migrate --noinput

uv run gunicorn \
    wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 6 \
    --threads 4
