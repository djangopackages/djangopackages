===========
Heroku
===========

Create a new git project
========================

* Create an empty git project
* Add a custom local_settings.py file
* Add open comparison as a git sub-module

Now begin the Heroku install process
==============================================

From the shell in the root::

    heroku create --stack cedar
    heroku addons:add shared-database:5mb    
    heroku addons:add memcache
    heroku addons:add sendgrid:starter
    git push heroku master