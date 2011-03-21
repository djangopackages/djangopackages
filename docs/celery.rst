================================
Optional Celery install & config
================================

Install redis (Mac)::

    brew install redis
    
Install redis (Ubuntu)::

    apt-get redis

Necessary changes to local_settings.py::

    CELERY_ALWAYS_EAGER = False
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    BROKER_BACKEND = "redis"
    BROKER_HOST = "localhost"
    BROKER_POST = 6379
    BROKER_VHOST = "0"
    
Start redis::

    redis-server

In a Packaginator shell enter to fire off queue::

    python manage.py shell
    >>> from pypi.tasks import queue_all_pypi_packages
    >>> queue_all_pypi_packages()
    
In another Packaginator shell::

    python manage.py celeryd -c 4
    