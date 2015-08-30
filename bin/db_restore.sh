#!/bin/bash
# restore a bacakup. arg is a filename that exitsts in backups dir

DOCKER_CONFIG=${DOCKER_CONFIG:-docker-compose-db.yml}
BACKUP_FILE=backups/$1

if ! [ -f $BACKUP_FILE ]; then
    echo "file not found"
    exit 1
fi

if [ $(docker-compose -f $DOCKER_CONFIG ps | grep "db" | grep "Up" | wc -l) != 0 ]; then
    echo "database container running. please stop before trying to restore"
    exit 1
fi

docker-compose -f $DOCKER_CONFIG run --rm psql dropdb -h db -U django django
docker-compose -f $DOCKER_CONFIG run --rm psql createdb -h db -U django -O django django
docker-compose -f $DOCKER_CONFIG run --rm psql pg_restore -Fc -h db -U django -d django $BACKUP_FILE
echo "backup restored"
