#!/bin/bash
# create a db backups to backups/

DOCKER_CONFIG=docker-compose-db.yml

BACKUP_FILE=django$1_$(date +'%Y_%m_%dT%H_%M_%S').bak
docker-compose -f $DOCKER_CONFIG run --rm psql pg_dump -Fc -h db -U $POSTGRES_USER -d django -f /backups/$BACKUP_FILE
echo "backup $BACKUP_FILE created"
