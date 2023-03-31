set dotenv-load := false

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

    if [ ! -f "docker-compose.override.yml" ]; then
        echo "docker-compose.override.yml created"
        cp docker-compose.override.yml.example docker-compose.override.yml
    fi

    docker-compose {{ ARGS }} build --force-rm

# Builds the Docker Images with optional arguments
@build *ARGS:
    docker-compose {{ ARGS }} build

# Builds the Docker Images with no optional arguments
@cibuild:
    just build

# Drop into the console on the docker image
@console:
    docker-compose run django /bin/bash

# Duplicates the `up` command
@server *ARGS="--detach":
    just up {{ ARGS }}

# Perform the initial setup for the Docker containers
@setup:
    just bootstrap

# Create a Superuser
@createsuperuser USERNAME EMAIL:
    docker-compose run django python manage.py createsuperuser \
        --username={{ USERNAME }} \
        --email={{ EMAIL }}

# Run the tests using the Django test runner
@test *ARGS="--no-input":
    docker-compose run django python manage.py test {{ ARGS }}

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
    docker-compose run --rm caddy caddy fmt -overwrite /etc/caddy/Caddyfile

# Is our Caddyfile valid?
@caddy-validate:
    docker-compose run --rm caddy caddy validate -adapter caddyfile -config /etc/caddy/Caddyfile

# --------------------------------------------------
# Docs recipes
# --------------------------------------------------
# @docs:
#     cd docs && make docs

@docs-down *ARGS:
    docker-compose --profile=docs down {{ ARGS }}

@docs-up *ARGS="--detach":
    docker-compose --profile=docs up {{ ARGS }}

@docs-update:
    pip-compile --resolver=backtracking docs/requirements.in

# --------------------------------------------------
# Deployment and production recipes
# --------------------------------------------------

# Deploys to production
@deploy:
    fab production deploy:stash=True
    fab production_2023 deploy

# Purge our CloudFlare cache
@purge_cache:
    docker-compose run django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache

# --------------------------------------------------
# Docker recipes
# --------------------------------------------------

# Bring down your docker containers
@down *ARGS:
    docker-compose down {{ ARGS }}

# Allows you to view the output from running containers
@logs *ARGS:
    docker-compose logs {{ ARGS }}

# Restart all services
@restart *ARGS:
    docker-compose restart {{ ARGS }}

# Start all services
@start *ARGS="--detach":
    docker-compose up {{ ARGS }}

@status:
    docker-compose ps

# Stop all services
@stop:
    docker-compose down

# Tail service logs
@tail:
    just logs --follow

# Bring up your Docker Containers
@up *ARGS="--detach":
    docker-compose up {{ ARGS }}

# --------------------------------------------------
# Django recipes
# --------------------------------------------------

# Run the collectstatic management command
@collectstatic *ARGS="--no-input":
    docker-compose run django python manage.py collectstatic {{ ARGS }}

# Run the tests with pytest
@pytest *ARGS:
    docker-compose run django pytest {{ ARGS }}

# Run the tests with pytest and generate coverage reports
@pytest-coverage *ARGS:
    docker-compose run django pytest \
        {{ ARGS }} \
        --cov-report html \
        --cov-report term:skip-covered \
        --cov .

# Run the shell management command
@shell *ARGS:
    docker-compose run django python manage.py shell {{ ARGS }}

# --------------------------------------------------
# Linter recipes
# --------------------------------------------------

# Check consistency of your env files
@lint:
    -modenv check
    -just lint-codespell

# Fixes common misspellings in text files
@lint-codespell:
    codespell --skip *.conf,*.csv,*.js*,./.git,./collected_static,./data,./docs/_*,./htmlcov,./static .

# Lints and formats all of your files using various formatters and linters
@lint-fmt:
    -unimport -r .
    -pyup-dirs --py37-plus .
    -black .
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
@pip-compile *ARGS:
    docker-compose run \
        --entrypoint= \
        --rm django \
            bash -c "pip install -U pip pip-tools && \
                pip-compile {{ ARGS }} requirements.in \
                    --generate-hashes \
                    --resolver=backtracking \
                    --output-file requirements.txt"

    docker-compose run \
        --entrypoint= \
        --rm django \
            bash -c "pip install -U pip pip-tools && \
                pip-compile {{ ARGS }} docs/requirements.in \
                    --generate-hashes \
                    --resolver=backtracking \
                    --output-file docs/requirements.txt"

# Upgrade existing Python dependencies to their latest versions
@pip-compile-upgrade:
    just pip-compile --upgrade

# Run pre-commit
@pre-commit *ARGS:
    pre-commit run {{ ARGS }}

@pre-commit-all-files:
    just pre-commit --all-files

# TODO: Make the target-version a variable

# Run `django-upgrade` with a target version of 4.1
@upgrade:
    git ls-files -- "*.py" | xARGS django-upgrade --target-version=4.1

# Run a management command as specified by ARGS
@management-command ARGS:
    docker-compose run --rm django python manage.py {{ ARGS }}

# Upgrade the PostgreSQL database

# TODO: Have the backup date be dynamic
@postgres-upgrade:
    docker-compose exec postgres psql --user djangopackages -d djangopackages < ../backups/backup_2021_09_21T19_00_10.sql

# TODO: Have the backup date be dynamic

# ???
@restore *ARGS:
    # TODO: change this to use DSLR...
    -PGPASSWORD=djangopackages dropdb --host=localhost --username=djangopackages djangopackages
    -PGPASSWORD=djangopackages createdb --host=localhost --username=djangopackages --owner=djangopackages djangopackages
    -PGPASSWORD=djangopackages createuser --host=localhost --username=doadmin
    -PGPASSWORD=djangopackages pg_restore -Fc --host=localhost --username=djangopackages -d djangopackages < ../backups/backup_2021_12_28.sql

    # docker-compose run --rm postgres dropdb --host=postgres --username=djangopackages djangopackages
    # docker-compose run --rm postgres createdb --host=postgres --username=djangopackages --owner=djangopackages djangopackages
    # docker-compose run --rm postgres pg_restore -Fc --host=postgres --username=djangopackages -d djangopackages < ../backups/backup_2021_12_28.sql

# new...

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
