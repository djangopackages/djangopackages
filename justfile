set dotenv-load := false

alias pip-compile := lock

DATABASE_URL := env_var_or_default('DATABASE_URL', 'postgres://djangopackages:djangopackages@postgres/djangopackages')

@_default:
    just --list

# Format the justfile
@fmt:
    just --fmt --unstable

# --------------------------------------------------
# script to rule them all recipes - start
# --------------------------------------------------

# Performs initial setup for Docker images and allows Arguments to be passed
bootstrap *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail

    if [ ! -f ".env.local" ]; then
        echo ".env.local created"
        cp .env.local.example .env.local
    fi

    docker compose {{ ARGS }} build --force-rm

# Builds the Docker Images with optional arguments
@build *ARGS:
    docker compose {{ ARGS }} build

# Builds the Docker Images with no optional arguments
@cibuild:
    just build

# Drop into the console on the docker image
@console:
    docker compose run django /bin/bash

# Duplicates the `up` command
@server *ARGS="--detach":
    just up {{ ARGS }}

# Perform the initial setup for the Docker containers
@setup:
    just bootstrap

# Create a Superuser
@createsuperuser USERNAME EMAIL:
    docker compose run django python manage.py createsuperuser \
        --username={{ USERNAME }} \
        --email={{ EMAIL }}

# Run the tests using the Django test runner
@test *ARGS="--no-input":
    docker compose run django python manage.py test {{ ARGS }}

# Once completed, it will run an update of *something*
@update:
    echo "TODO: update"

# --------------------------------------------------
# script to rule them all recipes - end
# --------------------------------------------------

# Update the version; Used before release to production
@bump *ARGS:
    bumpver update {{ ARGS }}

# --------------------------------------------------
# Caddy recipes
# --------------------------------------------------

# Format our Caddyfile
@caddy-fmt:
    docker compose run --rm caddy caddy fmt -overwrite /etc/caddy/Caddyfile

# Is our Caddyfile valid?
@caddy-validate:
    docker compose run --rm caddy caddy validate -adapter caddyfile -config /etc/caddy/Caddyfile

# --------------------------------------------------
# Docs recipes
# --------------------------------------------------
# @docs:
#     cd docs && make docs

@docs-down *ARGS:
    docker compose --profile=docs down {{ ARGS }}

@docs-up *ARGS="--detach":
    docker compose --profile=docs up {{ ARGS }}

@docs-update *ARGS:
    docker compose run \
        --entrypoint= \
        --rm django \
            bash -c "uv pip compile {{ ARGS }} docs/requirements.in \
                    --generate-hashes \
                    --output-file docs/requirements.txt"

# --------------------------------------------------
# Deployment and production recipes
# --------------------------------------------------

# Clear sessions
@clearsessions:
    fab production clearsessions

# Deploys to production
@deploy:
    fab production deploy

# Purge our CloudFlare cache
@purge_cache:
    docker compose run django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache

# --------------------------------------------------
# Docker recipes
# --------------------------------------------------

# Bring down your docker containers
@down *ARGS:
    docker compose down {{ ARGS }}

# Allows you to view the output from running containers
@logs *ARGS:
    docker compose logs {{ ARGS }}

# Restart all services
@restart *ARGS:
    docker compose restart {{ ARGS }}

# Start all services
@start *ARGS="--detach":
    docker compose up {{ ARGS }}

@status:
    docker compose ps

# Stop all services
@stop:
    docker compose down

# Tail service logs
@tail:
    just logs --follow

# Bring up your Docker Containers
@up *ARGS:
    docker compose up {{ ARGS }}

# --------------------------------------------------
# Django recipes
# --------------------------------------------------

# Run the collectstatic management command
@collectstatic *ARGS="--no-input":
    docker compose run django python manage.py collectstatic {{ ARGS }}

# Run the tests with pytest
@pytest *ARGS:
    docker compose run django pytest {{ ARGS }}

# Run the tests with pytest and generate coverage reports
@pytest-coverage *ARGS:
    docker compose run django pytest \
        {{ ARGS }} \
        --cov-report html \
        --cov-report term:skip-covered \
        --cov .

# Run the shell management command
@shell *ARGS:
    docker compose run django python manage.py shell {{ ARGS }}

# --------------------------------------------------
# Linter recipes
# --------------------------------------------------

# Check consistency of your env files
@lint:
    # TODO: consider bringing these back because they have some value
    # -modenv check
    # -just lint-codespell
    -just pre-commit-all-files

# Fixes common misspellings in text files
@lint-codespell:
    codespell --skip *.conf,*.csv,*.js*,./.git,./collected_static,./data,./docs/_*,./htmlcov,./static .

# Lints and formats all of your files using various formatters and linters
@lint-fmt:
    # TODO: verify/finish moving these into pre-commit
    -unimport -r .
    -pyup-dirs --py37-plus .
    -ruff format .
    -tryceratops .
    -djhtml -i templates/*.html templates/**/*.html templates/**/**/*.html

# --------------------------------------------------
# --------------------------------------------------

@cron:
    just management-command import_classifiers
    just management-command import_products
    just management-command import_releases
    just management-command packages_download_stats ./pypi.db

# --------------------------------------------------
# --------------------------------------------------

# A Linter for performance anti-patterns
@perflint:
    pipx run perflint ../djangopackages-git/ --load-plugins=perflint

# Compile new python dependencies
@lock *ARGS:
    docker compose run \
        --entrypoint= \
        --rm django \
            bash -c "uv pip compile {{ ARGS }} requirements.in \
                    --generate-hashes \
                    --output-file requirements.txt"

    docker compose run \
        --entrypoint= \
        --rm django \
            bash -c "uv pip compile {{ ARGS }} docs/requirements.in \
                    --generate-hashes \
                    --output-file docs/requirements.txt"

# Run pre-commit
@pre-commit *ARGS:
    pre-commit run {{ ARGS }}

@pre-commit-all-files:
    just pre-commit --all-files

# Upgrade existing Python dependencies to their latest versions
@upgrade:
    just lock --upgrade

# Run a management command as specified by ARGS
@management-command ARGS:
    docker compose run --rm django python manage.py {{ ARGS }}

# Remove current application services
@remove:
    ...

# --------------------------------------------------
# Tailwind CSS recipes
# --------------------------------------------------

@tailwind *ARGS:
    npx tailwindcss \
        --config ./static/js/tailwind.config.js \
        --input ./static/css/tailwindcss.css \
        --output ./static/css/tailwindcss.min.css \
        {{ ARGS }}

@tailwind-build:
    just tailwind build

@tailwind-lint:
    npx rustywind --check-formatted templates/
    # npx rustywind --write templates/

@tailwind-watch:
    just tailwind-build
    just tailwind --watch

# dump database to file
@pg_dump file='db.dump':
    docker compose run \
        --no-deps \
        --rm \
        postgres \
        pg_dump \
            --dbname "{{ DATABASE_URL }}" \
            --file /app/{{ file }} \
            --format=c \
            --verbose

# restore database dump from file
@pg_restore file='db.dump':
    docker compose run \
        --no-deps \
        --rm \
        postgres \
        pg_restore \
            --clean \
            --dbname "{{ DATABASE_URL }}" \
            --if-exists \
            --no-owner \
            --verbose \
            /app/{{ file }}
