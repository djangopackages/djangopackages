set dotenv-load := false

COMPOSE_FILE := "docker-compose.yml"

@_default:
    just --list

# script to rule them all - start

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

@build *ARGS:
    docker-compose {{ ARGS }} --file {{ COMPOSE_FILE }} build

@cibuild:
    just build

@console:
    docker-compose --file {{ COMPOSE_FILE }} run django /bin/bash

@server *ARGS="--detach":
    just up {{ ARGS }}

@setup:
    just bootstrap

@test *ARGS="--no-input":
    docker-compose --file {{ COMPOSE_FILE }} run django python manage.py test {{ ARGS }}

@update:
    echo "TODO: update"

# script to rule them all - end

@bump *ARGS:
    bumpver update {{ ARGS }}

@caddy-fmt:
    docker-compose run --rm caddy caddy fmt -overwrite /etc/caddy/Caddyfile

@caddy-validate:
    docker-compose run --rm caddy caddy validate -adapter caddyfile -config /etc/caddy/Caddyfile

@lint-codespell:
    codespell --skip *.conf,*.js*,./.git,./collected_static,./data,./static .

@deploy:
    fab production deploy

@down:
    docker-compose --file {{ COMPOSE_FILE }} down

@fmt:
    just --fmt --unstable

@lint:
    modenv check
    # just

@lint-fmt:
    -unimport -r .
    -pyup-dirs --py37-plus .
    -black .
    -tryceratops .
    -djhtml -i templates/*.html templates/**/*.html templates/**/**/*.html

@perflint:
    pipx run perflint ../djangopackages-git/ --load-plugins=perflint

# Compile new python dependencies
@pip-compile *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run --entrypoint= --rm django \
        bash -c "pip install -U pip pip-tools && \
            pip-compile {{ ARGS }} ./requirements.in --output-file ./requirements.txt --generate-hashes"

# Upgrade existing Python dependencies to their latest versions
@pip-compile-upgrade:
    just pip-compile --upgrade

@pre-commit:
    git ls-files -- . | xargs pre-commit run --config=./.pre-commit-config.yaml --files

@pytest *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run django pytest {{ ARGS }}

@pytest-coverage *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run django pytest \
        {{ ARGS }} \
        --cov-report html \
        --cov-report term:skip-covered \
        --cov .

@collectstatic *ARGS="--no-input":
    docker-compose --file {{ COMPOSE_FILE }} run django python manage.py collectstatic {{ ARGS }}

@shell *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} run django python manage.py shell {{ ARGS }}

@logs *ARGS:
    docker-compose --file {{ COMPOSE_FILE }} logs {{ ARGS }}

@restart *ARGS="--detach":
    just down
    just up {{ ARGS }}

@up *ARGS="--detach":
    docker-compose --file {{ COMPOSE_FILE }} up {{ ARGS }}

@upgrade:
    git ls-files -- "*.py" | xARGS django-upgrade --target-version=4.1

@searchv2_build:
    docker-compose --file {{ COMPOSE_FILE }} run --rm django python manage.py searchv2_build

@postgres-upgrade:
    docker-compose --file {{ COMPOSE_FILE }} exec postgres psql --user djangopackages -d djangopackages < ../backups/backup_2021_09_21T19_00_10.sql

@restore *ARGS:
    -PGPASSWORD=djangopackages dropdb --host=localhost --username=djangopackages djangopackages
    -PGPASSWORD=djangopackages createdb --host=localhost --username=djangopackages --owner=djangopackages djangopackages
    -PGPASSWORD=djangopackages createuser --host=localhost --username=doadmin
    -PGPASSWORD=djangopackages pg_restore -Fc --host=localhost --username=djangopackages -d djangopackages < ../backups/backup_2021_12_28.sql

    # docker-compose --file {{ COMPOSE_FILE }} run --rm postgres dropdb --host=postgres --username=djangopackages djangopackages
    # docker-compose --file {{ COMPOSE_FILE }} run --rm postgres createdb --host=postgres --username=djangopackages --owner=djangopackages djangopackages
    # docker-compose --file {{ COMPOSE_FILE }} run --rm postgres pg_restore -Fc --host=postgres --username=djangopackages -d djangopackages < ../backups/backup_2021_12_28.sql
