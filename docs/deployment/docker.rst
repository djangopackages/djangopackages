Deploy
======

- Install Docker & Docker Compose https://docs.docker.com/engine/installation/
- Install supervisord
- Install git
- Add to /etc/supervisor/supervisord.conf

[include]
files = /code/*/supervisord.conf /code/*/docker-supervisord.conf

Clone and build::

    mkdir /code
    git clone

-

# todo:

Backups
=======

To create a backup, run::

    docker-compose run postgres backup


To list backups, run::

    docker-compose run postgres list-backups


To restore a backup, run::

    docker-compose run postgres restore filename.sql


