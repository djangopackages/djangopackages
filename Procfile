web: gunicorn wsgi:application -b "0.0.0.0:$PORT" -w 3 --max-requests 1000 --settings=settings.heroku
worker: python worker.py
