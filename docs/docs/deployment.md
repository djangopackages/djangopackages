# Deployments

## Foreword

djangopackages.org uses Docker Compose for local development.

## Stack

Our `compose.yml` configuration contains the following services for local development:

- `postgres` powers our database (using pgautoupgrade for automatic version upgrades in local development).
- `django` powers our Python and Django backend, serving the app through the development server.
- `django-q` powers our task queues and background workers.
- `tailwind` watches and compiles Tailwind CSS during development.
- `utility` runs various commands including cron jobs to keep our `django*` services from blocking when we run one-off commands.
- `redis` provides caching.
- `docs` (profile: docs) runs our mkdocs server for documentation development.

## Clear our Media Cache

Our static media files are behind a CDN. We occasionally need to purge cached files. To purge the cache:

```shell
docker compose run django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache
```

Alternatively, you can use `just`

```shell
just purge_cache
```

## Troubleshooting

- Check if Docker is running:

  ```shell
  docker info
  ```

- Check if all services are running:

  ```shell
  docker compose ps
  ```

- View logs for all services:

  ```shell
  docker compose logs
  ```

  or with `just`:

  ```shell
  just logs
  ```

- Follow logs in real-time:

  ```shell
  docker compose logs --follow
  ```

  or with `just`:

  ```shell
  just tail
  ```

- Check logs for individual services:

  ```shell
  docker compose logs <service-name>
  ```

  Where `<service-name>` can be: `postgres`, `django`, `django-q`, `redis`, `tailwind`, or `docs`.
