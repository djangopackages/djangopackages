# Some helpful utility commands.

all:
	heroku pgbackups:capture --expire
	git push heroku master
	heroku run python manage.py syncdb --noinput  --settings=settings.heroku
	heroku run python manage.py migrate --settings=settings.heroku
	heroku run python manage.py collectstatic --noinput --settings=settings.heroku

deploy:
	heroku pgbackups:capture --expire
	git push heroku master
	heroku run python manage.py migrate package --settings=settings.heroku

style:
	git push heroku master
	heroku run python manage.py collectstatic --noinput --settings=settings.heroku

restoredata:
	heroku pgbackups:capture --expire
	curl -o -k latest.dump `heroku pgbackups:url`
	dropdb oc
	createdb oc
	pg_restore --verbose --clean --no-acl --no-owner -d oc latest.dump

createsite:
	heroku create --stack cedar
	heroku addons:add memcachier:dev
	heroku addons:add sendgrid:starter
	heroku addons:add heroku-postgresql:dev
	heroku addons:add pgbackups
	git push heroku master
	heroku ps:scale web=1
	heroku run python manage.py syncdb --noinput  --settings=settings.heroku
	heroku run python manage.py migrate --settings=settings.heroku

shell:
	heroku run python manage.py shell_plus --settings=settings.heroku