web: newrelic-admin run-program python manage.py run_gunicorn -b "0.0.0.0:$PORT" -w 3 --max-requests 1000 --settings=settings.heroku
worker: python worker.py

