#!/bin/sh
python -m manage migrate --noinput

python -m manage collectstatic --noinput

# /usr/local/bin/uwsgi \
#     --chdir /code \
#     --die-on-term \
#     --disable-write-exception \
#     --enable-threads \
#     --harakiri 120 \
#     --http :8000 \
#     --http-keepalive \
#     --http-timeout 60 \
#     --ignore-sigpipe \
#     --ignore-write-errors \
#     --listen 256 \
#     --master \
#     --max-requests 5000 \
#     --module wsgi:application \
#     --processes 4 \
#     --stats :1717 \
#     --threads 4 \
#     --vacuum

/usr/local/bin/gunicorn \
    wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 4
