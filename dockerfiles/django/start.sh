#!/bin/sh
python -m manage migrate --noinput

python -m manage collectstatic --noinput

/usr/local/bin/uwsgi \
    --chdir /code \
    --disable-write-exception \
    --enable-threads \
    --harakiri 120 \
    --http :5000 \
    --ignore-sigpipe \
    --ignore-write-errors \
    --master \
    --max-requests 5000 \
    --processes 4 \
    --single-interpreter \
    --stats :1717 \
    --wsgi-file /code/wsgi.py
