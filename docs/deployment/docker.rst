Server Provisioning
===================

There's a bootstrap script available, run::

    curl https://raw.githubusercontent.com/pydanny/djangopackages/master/server_bootstrap.sh

Backups
=======

To create a backup, run::

    docker-compose run postgres backup


To list backups, run::

    docker-compose run postgres list-backups


To restore a backup, run::

    docker-compose run postgres restore filename.sql



When Things Go Wrong
====================

- Is docker running?::

    service docker status


- Is supervisor and both daemonized processes running?::

    supervisorctl status

- Are all services running?::

    cd /code/djangopackages
    docker-compose ps
    docker-compose -f haproxy.yml ps

- Check the logs for all services::

    cd /code/djangopackages
    docker-compose logs
    docker-compose -f haproxy.yml logs

- Check the logs for individual services::

    cd /code/djangopackages
    docker-compose logs postgres|django|nginx|worker
    docker-compose -f haproxy.yml logs haproxy
