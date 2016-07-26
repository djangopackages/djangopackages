#!/bin/bash
# create a db backups to backups/

DOCKER_CONFIG=docker-compose-db.yml
BACKUP_FILE=django$1_$(date +'%Y_%m_%dT%H_%M_%S').bak
DATABASE_URL=postgres://postgresuser:mysecretpass@postgres:5432/postgresuser
echo DATABASE_URL
echo docker-compose -e DATABASE_URL=$DATABASE_URL run --rm psql pg_dump -Fc -h db -U postgresuser -d $DATABASE_URL -f /backups/$BACKUP_FILE

docker-compose -e DATABASE_URL=$DATABASE_URL run --rm psql pg_dump -Fc -h db -U postgresuser -d $DATABASE_URL -f /backups/$BACKUP_FILE
# docker-compose run -e DATABASE_URL=$DATABASE_URL --rm psql pg_dump -Fc -h db -U postgresuser -d $DATABASE_URL -f /backups/$BACKUP_FILE
echo "backup $BACKUP_FILE created"
