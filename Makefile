# Some helpful utility commands.

# make sure to replace this with the IP of your own server
DOCKER_SERVER=159.203.191.135

all: copy_secrets deploy migrate

bash:
	ssh root@$(DOCKER_SERVER)

migrate:
	# run python manage.py syncdb
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run django python manage.py syncdb --noinput'
	# run python manage.py migrate
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run django python manage.py migrate'

deploy: copy_secrets
	# build the stack
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose build'

	# stop the stack (supervisord will restart it)
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose stop'

copy_secrets:
	# copies the .env file and the key to the server
	scp .env root@$(DOCKER_SERVER):/code/djangopackages/.env

fetchnewdata:
	# run backup
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run postgres backup'
	# download latest backup
	scp root@$(DOCKER_SERVER):/data/djangopackages/backups/`ssh root@$(DOCKER_SERVER) ls -1t /data/djangopackages/backups/ | head -1` latest.dump
	dropdb oc
	createdb oc
	pg_restore --verbose --clean --no-acl --no-owner -j 2 -h localhost -d oc latest.dump

migrate_heroku_db_to_docker:
	# create a dump of the heroku db
	heroku pg:backups capture --app djangopackages
	# download the dump
	curl -o heroku.dump `heroku pg:backups public-url --app djangopackages`
	# convert the dump to raw sql
	pg_restore -f heroku.sql heroku.dump
	# copy the dump to the server
	scp heroku.sql root@$(DOCKER_SERVER):/data/djangopackages/backups/heroku.sql
	# restore dump
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run postgres restore heroku.sql'

migrate_db_to_new_home:
	#ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run postgres backup'
	scp root@$(DOCKER_SERVER):/data/djangopackages/backups/`ssh root@$(DOCKER_SERVER) ls -1t /data/djangopackages/backups/ | head -1` latest.dump
	scp -P 56565 latest.dump root@docker2.server.wtf:/data-slow/djangopackages/backups/latest.dump
	ssh root@docker2.server.wtf -p56565 -C 'cd /code/djangopackages && docker-compose run postgres restore latest.dump'

shell:
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run django python manage.py shell_plus'

runcron:
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run django python manage.py pypi_updater'
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run django python manage.py package_updater'
	ssh root@$(DOCKER_SERVER) -C 'cd /code/djangopackages && docker-compose run django python manage.py searchv2_build'

test:
	python manage.py test --settings=settings.test
