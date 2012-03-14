==========
Deployment
==========

deploying to heroku::

    heroku create --stack cedar
    git push heroku master
    heroku addons:add heroku-shared-postgresql
    heroku pg:promote HEROKU_SHARED_POSTGRESQL_<database-name>
    heroku pg:psql HEROKU_SHARED_POSTGRESQL_<database-name>
    \i django_oc.sql
    heroku run python manage.py collectstatic --noinput --settings=settings.prod