# Deployments

## Foreword

djangopackages.org use Docker Compose both for local development and in production.

The current strategy is:

- Use a virtual machine with a well patched OS (debian or ubuntu), djangopackages.org is using
- Install Docker, Docker Compose, git, and supervisord (manages Docker)
- Clone the code on the server
- Start our services

## Stack

All of our `compose*.yml` configurations contains the following services:

- `postgres` powers our database.
- `django` powers our Python and Django backend. In production we use call these `django-a` and `django-b` to run our WSGI server and serves the app through gunicorn.
- `django-q` powers our task queues and background workers.
- `utility` runs our various commands including cron jobs to keep our `django*` services from blocking when we run one-off commands.
- `caddy` (production only) proxies incoming requests to the gunicorn server
- `redis` as cache
- `docs` (local only) runs our mkdocs server so we can work on docs.

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

## Clear our Media Cache

Our static media files are behind a CDN. We occasionally need to purge cached files. To purge the cache:

```shell
docker compose run django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache
```

Alternatively, you can use `just`

```shell
just purge_cache
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
  docker compose ps
  ```

- Check the logs for all services:

  ```shell
  cd /code/djangopackages
  docker compose logs
  ```

- Check the logs for individual services:

  ```shell
  cd /code/djangopackages
  docker compose logs postgres|django-a|django-b|caddy
  ```

[Fabric]: https://www.fabfile.org/
