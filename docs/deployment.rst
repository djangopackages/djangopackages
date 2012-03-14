deploying to heroku::

    heroku create --stack cedar
    git push heroku master
    heroku addons:add heroku-shared-postgresql
    heroku pg:promote HEROKU_SHARED_POSTGRESQL_BROWN
    heroku pg:psql HEROKU_SHARED_POSTGRESQL_BROWN
    \i django_oc.sql