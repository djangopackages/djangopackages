set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Don't load environment variables from .env file

set dotenv-load := false

# Create an alias for pip-compile to use the lock recipe

alias pip-compile := lock

# Set the database URL with a default value if not in environment

DATABASE_URL := env_var_or_default('DATABASE_URL', 'postgres://djangopackages:djangopackages@postgres/djangopackages')

# --------------------------------------------------
# Core Utilities
# --------------------------------------------------

# Show list of available recipes when just is run without arguments
[group('utils')]
@_default:
    just --list

# Format the justfile
[group('utils')]
@fmt:
    just --fmt --unstable

# Update the version; Used before release to production
[group('utils')]
@bump *ARGS:
    uv --quiet tool run \
        bumpver update {{ ARGS }}

# --------------------------------------------------
# Setup and Environment
# --------------------------------------------------

# Performs initial setup for Docker images and allows Arguments to be passed
[group('utils')]
bootstrap *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if virtual environment exists (looking for bin/activate)
    if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        echo "Virtual environment already exists"
    else
        echo "Creating virtual environment using uv..."
        uv venv
        echo "Virtual environment created successfully"
    fi

    uv pip install --upgrade pip uv

    if [ ! -f ".env.local" ]; then
        echo ".env.local created"
        cp .env.local.example .env.local
    fi

    docker compose {{ ARGS }} build --force-rm

# Perform the initial setup for the Docker containers
[group('utils')]
@setup:
    just bootstrap

# Compile new python dependencies
[group('utils')]
@lock *ARGS:
    uv pip compile \
        {{ ARGS }} \
        requirements.in \
        --generate-hashes \
        --output-file requirements.txt

    uv pip compile \
        {{ ARGS }} \
        docs/requirements.in \
        --generate-hashes \
        --output-file docs/requirements.txt

# Upgrade existing Python dependencies to their latest versions
[group('utils')]
@upgrade:
    just lock --upgrade

# --------------------------------------------------
# Docker Containers
# --------------------------------------------------

# Builds the Docker Images with optional arguments
[group('docker')]
@build *ARGS:
    docker compose {{ ARGS }} build

# Builds the Docker Images with no optional arguments
[group('docker')]
@cibuild:
    just build

# Bring down your docker containers
[group('docker')]
@down *ARGS:
    docker compose down {{ ARGS }}

# Allows you to view the output from running containers
[group('docker')]
@logs *ARGS:
    docker compose logs {{ ARGS }}

# Restart all services
[group('docker')]
@restart *ARGS:
    docker compose restart {{ ARGS }}

# Start all services
[group('docker')]
@start *ARGS="--detach":
    docker compose up {{ ARGS }}

# Show status of running containers
[group('docker')]
@status:
    docker compose ps

# Stop all services
[group('docker')]
@stop:
    docker compose down

# Tail service logs
[group('docker')]
@tail:
    just logs --follow

# Bring up your Docker Containers
[group('docker')]
@up *ARGS:
    docker compose up {{ ARGS }}

# Duplicates the `up` command
[group('docker')]
@server *ARGS="--detach":
    just up {{ ARGS }}

# Remove all application services and volumes
[group('docker')]
@remove:
    echo "TODO: remove"

# --------------------------------------------------
# Django Management
# --------------------------------------------------

# Drop into the console on the docker image
[group('django')]
@console:
    docker compose run --rm django /bin/bash

# Create a Superuser
[group('django')]
@createsuperuser USERNAME EMAIL:
    docker compose run --rm django python manage.py createsuperuser \
        --username={{ USERNAME }} \
        --email={{ EMAIL }}

# Run the collectstatic management command
[group('django')]
@collectstatic *ARGS="--no-input":
    docker compose run --rm django python manage.py collectstatic {{ ARGS }}

# Run the shell management command
[group('django')]
@shell *ARGS:
    docker compose run --rm django python manage.py shell {{ ARGS }}

# Run a management command as specified by ARGS
[group('django')]
@management-command ARGS:
    docker compose run --rm --rm django python manage.py {{ ARGS }}

# Run all scheduled tasks in sequence
[group('django')]
@cron:
    just management-command import_classifiers
    just management-command import_products
    just management-command import_releases
    just management-command packages_download_stats ./pypi.db

# Once completed, it will run an update of *something*
[group('utils')]
@update:
    echo "TODO: update"

# --------------------------------------------------
# Testing
# --------------------------------------------------

# Run the tests using the Django test runner
[group('testing')]
@test *ARGS="--no-input":
    docker compose run --rm django python manage.py test {{ ARGS }}

# Run the tests with pytest
[group('testing')]
@pytest *ARGS:
    docker compose run --rm django pytest {{ ARGS }}

# Run the tests with pytest and generate coverage reports
[group('testing')]
@pytest-coverage *ARGS:
    docker compose run --rm django pytest \
        {{ ARGS }} \
        --cov-report html \
        --cov-report term:skip-covered \
        --cov .

# --------------------------------------------------
# Linting and Code Quality
# --------------------------------------------------

# Check consistency of your env files
[group('linting')]
@lint:
    # TODO: consider bringing these back because they have some value
    # -modenv check
    # -just lint-codespell
    -just pre-commit-all-files

# Fixes common misspellings in text files
[group('linting')]
@lint-codespell:
    uv --quiet tool run \
        codespell -I .codespellignore .

# A Linter for performance anti-patterns
[group('linting')]
@perflint:
    uv --quiet tool run \
        perflint ../djangopackages-git/ \
        --load-plugins=perflint

# Run pre-commit hooks with specified arguments
[group('linting')]
@pre-commit *ARGS:
    uv tool run \
        --with pre-commit-uv \
        pre-commit run {{ ARGS }}

# Run pre-commit hooks on all files
[group('linting')]
@pre-commit-all-files:
    just pre-commit --all-files

# --------------------------------------------------
# Database Operations
# --------------------------------------------------

# dump database to file
[group('database')]
@pg_dump file='db.dump':
    docker compose run --rm \
        --no-deps \
        --rm \
        postgres \
        pg_dump \
            --dbname "{{ DATABASE_URL }}" \
            --file /code/{{ file }} \
            --format=c \
            --verbose

# restore database dump from file
[group('database')]
@pg_restore file='db.dump':
    docker compose run --rm \
        --no-deps \
        --rm \
        postgres \
        pg_restore \
            --clean \
            --dbname "{{ DATABASE_URL }}" \
            --if-exists \
            --no-owner \
            --verbose \
            /code/{{ file }}

# Clear sessions
[group('django')]
[group('server-admin')]
@clearsessions:
    uv --quiet tool run \
        --python=3.9 \
        --with Fabric3 \
        --with rich \
        fab production clearsessions

# --------------------------------------------------
# Frontend Development
# --------------------------------------------------

# Process Tailwind CSS with optional arguments. Requires the file `./static/js/tailwind.config.js` to exist.
[group('frontend')]
[group('experimental')]
@tailwind *ARGS:
    npx tailwindcss \
        --config ./static/js/tailwind.config.js \
        --input ./static/css/tailwindcss.css \
        --output ./static/css/tailwindcss.min.css \
        {{ ARGS }}

# Build Tailwind CSS once. Requires the file `./static/js/tailwind.config.js` to exist.
[group('frontend')]
[group('experimental')]
@tailwind-build:
    just tailwind build

# Check for proper Tailwind CSS class ordering. Requires the file `./static/js/tailwind.config.js` to exist.
[group('frontend')]
[group('experimental')]
@tailwind-lint:
    npx rustywind --check-formatted templates/
    # npx rustywind --write templates/

# Build and then watch for Tailwind CSS changes. Requires the file `./static/js/tailwind.config.js` to exist.
[group('frontend')]
[group('experimental')]
@tailwind-watch:
    just tailwind-build
    just tailwind --watch

# --------------------------------------------------
# Documentation
# --------------------------------------------------

# Stop documentation services
[group('docs')]
@docs-down *ARGS:
    docker compose --profile=docs down {{ ARGS }}

# Start documentation services
[group('docs')]
@docs-up *ARGS="--detach":
    docker compose --profile=docs up {{ ARGS }}

# Update documentation dependencies
[group('docs')]
@docs-update *ARGS:
    uv --quiet pip compile \
        {{ ARGS }} \
        docs/requirements.in \
        --generate-hashes \
        --output-file docs/requirements.txt

# --------------------------------------------------
# Server Configuration
# --------------------------------------------------

# Format our Caddyfile. Must be run with the `compose.prod.yml` compose file.
[group('server')]
@caddy-fmt:
    docker compose run --rm caddy caddy fmt -overwrite /etc/caddy/Caddyfile

# Is our Caddyfile valid? Must be run with the `compose.prod.yml` compose file.
[group('server')]
@caddy-validate:
    docker compose run --rm caddy caddy validate -adapter caddyfile -config /etc/caddy/Caddyfile

# --------------------------------------------------
# Deployment
# --------------------------------------------------

# Deploys to production. Requires root access to the server.
[group('deployment')]
[group('server-admin')]
@deploy:
    uv --quiet tool run \
        --python=3.9 \
        --with Fabric3 \
        --with rich \
        fab production deploy

# Purge our CloudFlare cache
[group('deployment')]
[group('server-admin')]
@purge_cache:
    docker compose run --rm django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache
