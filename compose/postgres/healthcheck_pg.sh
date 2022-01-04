#!/bin/bash
set -eo pipefail
# based on https://github.com/docker-library/healthcheck/blob/master/postgres/docker-healthcheck
# If the healthcheck is configured on the Dockerfile or docker-compose.yml
# use the docker inspect to show the healthcheck logs:
# docker inspect --format "{{json .State.Health }}" <container name> | jq

host="$(hostname -i || echo '127.0.0.1')"
user="${POSTGRES_USER:-postgres}"
db="${POSTGRES_DB:-POSTGRES_USER}"
port="${POSTGRES_PORT:-5432}"
export PGPASSWORD="${POSTGRES_PASSWORD:-}"

args=(
	# force postgres to not use the local unix socket (test "external" connectibility)
	--host "$host"
	--port "$port"
	--username "$user"
	--dbname "$db"
	--quiet --no-align --tuples-only
)

if select="$(echo 'SELECT 1' | psql "${args[@]}")" && [ "$select" = '1' ]; then
	echo "Health check: PostgreSQL is running as expected. ";
	exit 0;
fi

echo "Health check: PostgreSQL is down.";
exit 1
