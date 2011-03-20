===============
Celery
===============

Install redis (Mac)::

    brew install redis
    
Install redis (Ubuntu)::

    apt-get redis

local_settings::

    CELERY_ALWAYS_EAGER = False
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    BROKER_BACKEND = "redis"
    BROKER_HOST = "localhost"
    BROKER_POST = 6379
    BROKER_VHOST = "0"

Packaginator shell commands to get all packages::

    from pypi import slurper
    s = slurper.Slurper(all_packages=True)
    s.get_or_create_all_packages()
    
In another Packaginator shell::

    python manage.py celeryd -c 4
    