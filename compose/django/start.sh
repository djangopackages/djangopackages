#!/bin/sh
python manage.py migrate
python /app/manage.py collectstatic --noinput
/usr/local/bin/uwsgi --http :5000 \
    --wsgi-file /app/wsgi.py \
    --master \
    --processes 3 \
    --chdir /app \
    --harakiri 120 \
    --stats :1717 \
    --enable-threads \
    --single-interpreter \
    --max-requests 5000
