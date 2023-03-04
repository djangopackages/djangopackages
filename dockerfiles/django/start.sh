#!/bin/sh
python /app/manage.py migrate --noinput
python /app/manage.py collectstatic --noinput
/usr/local/bin/uwsgi \
    --chdir /app \
    --disable-write-exception \
    --enable-threads \
    --harakiri 120 \
    --http :5000 \
    --ignore-sigpipe \
    --ignore-write-errors \
    --master \
    --max-requests 5000 \
    --processes 3 \
    --single-interpreter \
    --stats :1717 \
    --wsgi-file /app/wsgi.py
