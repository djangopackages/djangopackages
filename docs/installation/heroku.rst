===========
Heroku
===========

From the shell::

    heroku create --stack cedar
    heroku addons:add shared-database:5mb    
    heroku addons:add memcache
    heroku addons:add sendgrid:starter
