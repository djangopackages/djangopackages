===========
Heroku
===========

Quick and Easy Heroku Deployment
=================================

This is meant for setting up test and QA servers, not full deployments.

If you have Heroku Toolbelt installed and are on Mac OS X or Linux, you can run the following from your repo:

.. sourcecode:: bash

    make createsite


Real Heroku Deployment
=====================================

Deploying to heroku:

.. sourcecode:: bash

    heroku create --stack cedar
    git push heroku master
    heroku addons:add heroku-shared-postgresql
    heroku addons:add memcachier:dev
    heroku addons:add sendgrid:starter    
    heroku addons:add scheduler:standard
    heroku pg:promote HEROKU_SHARED_POSTGRESQL_GOLD
    heroku pg:psql HEROKU_SHARED_POSTGRESQL_GOLD
    \i django_oc.sql
    
Chron Jobs that need to be set up
---------------------------------

Sample::
    
    python manage.py pypi_updater --settings=settings.heroku
    python manage.py repo_updater --settings=settings.heroku
    python manage.py searchv2_build --settings=settings.heroku
    
TODO: Email admins with the log

Custom settings that need to be added
-------------------------------------

Do the following:

.. sourcecode:: bash

    heroku config:add SECRET_KEY=<random-key>
    heroku config:add GITHUB_API_SECRET=CUSTOM
    heroku config:add GITHUB_APP_ID=CUSTOM
    heroku config:add SITE_TITLE=Django Packages
    heroku config:add FRAMEWORK_TITLE=Django
    heroku config:add AWS_ACCESS_KEY_ID=CUSTOM 
    heroku config:add AWS_SECRET_ACCESS_KEY=CUSTOM
    heroku config:add AWS_STORAGE_BUCKET_NAME=CUSTOM    