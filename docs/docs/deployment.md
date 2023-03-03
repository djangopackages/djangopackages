# Deployments

## Foreword

As of beginning 2016 the docker toolset is not quite there to provide a heroku like experience
when deploying to production. A lot of parts are already there, but have a few quirks that need
to be addressed.

Because of that, the deployment strategy for djangopackages.org is a bit different from what you
read in the getting started with docker tutorials.

First, we don't use docker-machine. It's not reliable and has no team of maintainers comparable
to other distros like debian, ubuntu or rhel that manages security releases.

Second, there's no way do daemonize the docker compose process. When the underlying VM is
restarted, the stack won't start automatically.

The current strategy is:

> - Use a virtual machine with a well patched OS (debian, ubuntu, RHEL), djangopackages.org is using
>   ubuntu 14.04
> - Install docker, docker-compose, git and supervisord
> - Clone the code on the server
> - Let supervisord run it

## Stack

The configuration in `docker-compose.yml` contains 4 services:

> - `postgres` that powers the database
> - `django-a` and `django-b` that runs the WSGI server and serves the app through gunicorn
> - `caddy` that proxies incoming requests to the gunicorn server
> - `redis` as cache

## Deploy code changes

Website releases are managed through [Fabric].
When the `deploy` command is ran, Fabric will SSH to our production server, pull the latest changes from our GitHub repository, build a new Docker image, and then perform a blue/green deploy with our new container image.

```shell
fab deploy
```

or via `just`:

```shell
just deploy
```

## Backups

To create a backup, run:

```shell
docker-compose run postgres backup
```

To list backups, run:

```shell
docker-compose run postgres list-backups
```

To restore a backup, run:

```shell
docker-compose run postgres restore filename.sql
```

Backups are located at `/data/djangopackages/backups` as plain SQL files.

## Clear our Media Cache

Our static media files are behind a CDN. We occasionally need to purge cached files. To purge the cache:

```shell
docker-compose run django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache
```

Alternatively, you can use `just`

```shell
just purge_cache:
```

## When Things Go Wrong

- Is docker running?:

  ```shell
  service docker status
  ```

- Is supervisor and both daemonized processes running?:

  ```shell
  supervisorctl status
  ```

- Are all services running?:

  ```shell
  cd /code/djangopackages
  docker-compose ps
  ```

- Check the logs for all services:

  ```shell
  cd /code/djangopackages
  docker-compose logs
  ```

- Check the logs for individual services:

  ```shell
  cd /code/djangopackages
  docker-compose logs postgres|django-a|django-b|caddy
  ```

[Fabric]: https://www.fabfile.org/
