# Some helpful utility commands.

all:
	heroku pg:backups capture --app djangopackages
	git push heroku master
	heroku run python manage.py syncdb --noinput  --settings=settings.heroku
	heroku run python manage.py migrate --settings=settings.heroku
	heroku run python manage.py collectstatic --noinput --settings=settings.heroku

deploy:
	heroku pg:backups capture --app djangopackages
	git push heroku master
	heroku run python manage.py migrate searchv2 --settings=settings.heroku --app djangopackages

style:
	git push heroku master --app djangopackages
	heroku run python manage.py collectstatic --noinput --settings=settings.heroku --app djangopackages

restoredata:
	# heroku pgbackups:capture --expire
	heroku pg:backups capture --app=djangopackages
	# curl -o -k latest.dump `heroku pgbackups:url`
	curl -o latest.dump `heroku pg:backups public-url --app=djangopackages`
	dropdb oc
	createdb oc
	# pg_restore --clean --no-acl --no-owner -d oc latest.dump > /dev/null 2>&1
	# pg_restore --verbose --clean --no-acl --no-owner -j 2 -h localhost -U myuser -d mydb latest.dump
	pg_restore --verbose --clean --no-acl --no-owner -j 2 -h localhost -d oc latest.dump

createsite:
	heroku create --stack cedar
	heroku addons:add memcachier:dev
	heroku addons:add sendgrid:starter
	heroku addons:add heroku-postgresql:dev
	heroku addons:add pgbackups
	heroku addons:add redistogo
	git push heroku master
	heroku ps:scale web=1
	heroku run python manage.py syncdb --noinput  --settings=settings.heroku
	heroku run python manage.py migrate --settings=settings.heroku

shell:
	heroku run python manage.py shell_plus --settings=settings.heroku

runcron:
	heroku run python manage.py pypi_updater --settings=settings.heroku
	heroku run python manage.py repo_updater --settings=settings.heroku
	heroku run python manage.py searchv2_build --settings=settings.heroku

test:
	python manage.py test --settings=settings.test

cull:
	heroku run python manage.py delete_old_sessions --settings=settings.heroku --app=djangopackages

docker_restore:
	docker-compose run postgres pg_restore --verbose --clean -j 2 latest.dump

docker_create:
	docker-machine create --driver digitalocean --digitalocean-access-token $DO prod2
	eval "$(docker-machine env prod2)"
	docker-compose build
	docker-compose up -d
