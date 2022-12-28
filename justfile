set dotenv-load := false

COMPOSE_FILE := "docker-compose.yml"

@_default:
    just --list

# script to rule them all - start

# Performs intial setup for Docker images and allows Arguments to be passed
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

    docker-compose {{ ARGS }} --file {{ COMPOSE_FILE }} build --force-rm

# Builds the Docker Images with optional arguments
@build *ARGS:
    docker-compose {{ ARGS }} --file {{ COMPOSE_FILE }} build

# Builds the Docker Images with no optional arguments
@cibuild:
    just build

# Drop into the console on the docker image
@console:
    docker-compose --file {{ COMPOSE_FILE }} run django /bin/bash

# Duplicates the `up` command
@server *ARGS="--detach":
    just up {{ ARGS }}

# Perform the inital setup for the Docker containers
@setup:
    just bootstrap

# Run the tests using the Django test runner
@test *ARGS="--no-input":
    docker-compose --file {{ COMPOSE_FILE }} run django python manage.py test {{ ARGS }}

# Once completed, it will run an update of *something*
@update:
    echo "TODO: update"

# script to rule them all - end

# Update the version; Used before release to production
@bump *ARGS:
    bumpver update {{ ARGS }}

# ???
@caddy-fmt:
    docker-compose run --rm caddy caddy fmt -overwrite /etc/caddy/Caddyfile

# ???
@caddy-validate:
    docker-compose run --rm caddy caddy validate -adapter caddyfile -config /etc/caddy/Caddyfile

# Fixes common misspellings in text files
@lint-codespell:
    codespell --skip *.conf,*.js*,./.git,./collected_static,./data,./static .

# Deploys to production
@deploy:
    fab production deploy

# Bring down your docker containers
@down:
    docker-compose --file {{ COMPOSE_FILE }} down

# Format the justfile
@fmt:
    just --fmt --unstable

# Check consistency of your env files
@lint:
    modenv check
    # just

# Lints and formats all of your files using various formatters and linters
@lint-fmt:
    -unimport -r .
    -pyup-dirs --py37-plus .
    -black .
    -tryceratops .
    -djhtml -i templates/*.html templates/**/*.html templates/**/**/*.html

# A Linter for performance anti-patterns
@perflint:
    pipx run perflint ../djangopackages-git/ --load-plugins=perflint

# Compile new python dependencies
@pip-compile *ARGS:
    docker-compose run \
        --entrypoint= \
        --rm django \
            bash -c "pip install -U pip && \
                pip-compile {{ ARGS }} ./requirements.in \
                    --generate-hashes \
                    --output-file ./requirements.txt"

# Upgrade existing Python dependencies to their latest versions
@pip-compile-upgrade:
    just pip-compile --upgrade

# Upgrade existing packages and Install pipx packages needed for development
@pipx-install:
    pipx upgrade-all
    pipx install djhtml
    pipx install tryceratops
    pipx install black
    pipx install unimport
    pipx install pyupgrade-directories

# Run pre-commit
@pre-commit:
    git ls-files -- . | xargs pre-commit run --config=./.pre-commit-config.yaml --files

@purge_cache:
    docker-compose --file {{ COMPOSE_FILE }} run django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache

# Run the tests with pytest
@pytest *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run django pytest {{ ARGS }}

# Run the tests with pytest and generate coverage reports
@pytest-coverage *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run django pytest \
        {{ ARGS }} \
        --cov-report html \
        --cov-report term:skip-covered \
        --cov .

# Run the collectstatic management command
@collectstatic *ARGS="--no-input":
    docker-compose --file {{ COMPOSE_FILE }} run django python manage.py collectstatic {{ ARGS }}

# Run the shell management command
@shell *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run django python manage.py shell {{ ARGS }}

# Allows you to view the output from running containers
@logs *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} logs {{ ARGS }}

# Restart your Docker containers
@restart *ARGS="--detach":
    just down
    just up {{ ARGS }}

# Bring up your Docker Containers
@up *ARGS="--detach":
    docker-compose --file {{ COMPOSE_FILE }} up {{ ARGS }}

# TODO: Make the target-version a variable

# Run `django-upgrade` with a target version of 4.1
@upgrade:
    git ls-files -- "*.py" | xARGS django-upgrade --target-version=4.1

# Run a management command as specified by ARGS
@management-command ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run --rm django python manage.py {{ ARGS }}

# Upgrade the PostgreSQL database

# TODO: Have the backup date be dynamic
@postgres-upgrade:
    docker-compose --file {{ COMPOSE_FILE }} exec postgres psql --user djangopackages -d djangopackages < ../backups/backup_2021_09_21T19_00_10.sql

# Create a Superuser
@superuser USERNAME EMAIL:
    docker-compose -f {{ COMPOSE_FILE }} run django python manage.py createsuperuser --username={{ USERNAME }} --email={{ EMAIL }}

# TODO: Have the backup date be dynamic

# ???
@restore *ARGS:
    -PGPASSWORD=djangopackages dropdb --host=localhost --username=djangopackages djangopackages
    -PGPASSWORD=djangopackages createdb --host=localhost --username=djangopackages --owner=djangopackages djangopackages
    -PGPASSWORD=djangopackages createuser --host=localhost --username=doadmin
    -PGPASSWORD=djangopackages pg_restore -Fc --host=localhost --username=djangopackages -d djangopackages < ../backups/backup_2021_12_28.sql

    # docker-compose --file {{ COMPOSE_FILE }} run --rm postgres dropdb --host=postgres --username=djangopackages djangopackages
    # docker-compose --file {{ COMPOSE_FILE }} run --rm postgres createdb --host=postgres --username=djangopackages --owner=djangopackages djangopackages
    # docker-compose --file {{ COMPOSE_FILE }} run --rm postgres pg_restore -Fc --host=postgres --username=djangopackages -d djangopackages < ../backups/backup_2021_12_28.sql
