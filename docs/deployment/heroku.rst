===========
Heroku
===========


Now begin the Heroku install process
==============================================

Deploying to heroku:

.. sourcecode:: bash

    heroku create --stack cedar
    git push heroku master
    heroku addons:add heroku-shared-postgresql
    heroku addons:add memcache
    heroku addons:add sendgrid:starter    
    heroku pg:promote HEROKU_SHARED_POSTGRESQL_BROWN
    heroku pg:psql HEROKU_SHARED_POSTGRESQL_BROWN
    \i django_oc.sql

Custom settings that need to be added
=======================================

Do the following:

.. sourcecode:: bash

    heroku config:add SECRET_KEY=<random-key>
    heroku config:add GITHUB_API_SECRET=<your-github-api-secret>
    heroku config:add GITHUB_APP_ID=<your-github-app-id>
    heroku config:add S3_KEY=<your-s3-key>  
    heroku config:add S3_SECRET=<your-s3-secret>  
    heroku config:add SITE_TITLE=Django Packages
    heroku config:add FRAMEWORK_TITLE=Django