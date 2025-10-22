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

# Perform initial setup: create venv, .env.local, and build Docker images
[group('utils')]
bootstrap *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if virtual environment exists (looking for bin/activate)
    if [ "${VIRTUAL_ENV:-}" ]; then
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

# Alias for bootstrap - perform initial setup
[group('utils')]
@setup:
    just bootstrap

# Compile Python dependencies with hashes
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

# Build Docker images for CI
[group('docker')]
@cibuild:
    just build

# Bring down Docker containers
[group('docker')]
@down *ARGS:
    docker compose down {{ ARGS }}

# View output from running containers
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

# Start Docker containers
[group('docker')]
@up *ARGS:
    docker compose up {{ ARGS }}

# Alias for up - start Docker containers
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

# Drop into a bash shell in the Django container
[group('django')]
@console:
    docker compose run --rm django /bin/bash

# Create a Django superuser
[group('django')]
@createsuperuser USERNAME EMAIL:
    docker compose run --rm django python manage.py createsuperuser \
        --username={{ USERNAME }} \
        --email={{ EMAIL }}

# Collect static files
[group('django')]
@collectstatic *ARGS="--no-input":
    docker compose run --rm django python manage.py collectstatic {{ ARGS }}

# Run Django shell
[group('django')]
@shell *ARGS:
    docker compose run --rm django python manage.py shell {{ ARGS }}

# Run a Django management command
[group('django')]
@run ARGS:
    docker compose run --rm django python manage.py {{ ARGS }}

# Run scheduled data import tasks
[group('django')]
@cron:
    just run import_classifiers
    just run import_products
    just run import_releases
    just run packages_download_stats ./pypi.db

# --------------------------------------------------
# Testing
# --------------------------------------------------

# Run tests using Django test runner
[group('testing')]
@test *ARGS="--no-input":
    docker compose run --rm django python manage.py test {{ ARGS }}

# Run tests with pytest
[group('testing')]
@pytest *ARGS:
    docker compose run --rm django pytest {{ ARGS }}

# Run tests with pytest and generate coverage reports
[group('testing')]
@coverage *ARGS:
    docker compose run --rm django pytest \
        {{ ARGS }} \
        --cov-report html \
        --cov-report term:skip-covered \
        --cov .

# --------------------------------------------------
# Linting and Code Quality
# --------------------------------------------------

# Run all pre-commit linting and code quality checks
[group('linting')]
@lint *ARGS:
    uv tool run \
        --with pre-commit-uv \
        pre-commit run --all-files {{ ARGS }}

# Check for performance anti-patterns
[group('linting')]
@perflint:
    uv --quiet tool run \
        perflint ../djangopackages-git/ \
        --load-plugins=perflint

# --------------------------------------------------
# Database Operations
# --------------------------------------------------

# Dump database to file
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

# Restore database from dump file
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

# Clear Django sessions on production server
[group('production')]
@clearsessions:
    uv --quiet tool run \
        --python=3.9 \
        --with Fabric3 \
        --with rich \
        fab production clearsessions

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

# Format Caddyfile (requires compose.prod.yml)
[group('server')]
@caddy-fmt:
    docker compose run --rm caddy caddy fmt -overwrite /etc/caddy/Caddyfile

# Validate Caddyfile (requires compose.prod.yml)
[group('server')]
@caddy-validate:
    docker compose run --rm caddy caddy validate -adapter caddyfile -config /etc/caddy/Caddyfile

# --------------------------------------------------
# Production
# --------------------------------------------------

# Deploy to production server (requires root access)
[group('production')]
@deploy:
    uv --quiet tool run \
        --python=3.9 \
        --with Fabric3 \
        --with rich \
        fab production deploy

# Purge Cloudflare cache
[group('production')]
@purge_cache:
    docker compose run --rm django cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache
