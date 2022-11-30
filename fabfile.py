"""
This is a collection of useful utility functions when working with docker on different environments.
In order to use these functions, install fabric on your local machine with::
    pip install fabric
Please note: Fabric is a remote code execution tool, NOT a remote configuration tool. While you can copy files
from here to there, it is not a good replacement for salt or ansible in this regard.
There is a function called `production` where you need to fill in the details about your production machine(s).
You can then run::
    fab production status
to get the status of your stack
To list all available commands, run::
    fab -l
"""


import time
from fabric.api import *  # noqa
from fabric.api import cd
from fabric.api import env
from fabric.api import lcd
from fabric.colors import blue
from fabric.operations import local as lrun, run, put


def local():
    """
    Work on the local environment
    """
    env.compose_file = "docker-compose.yml"
    env.project_dir = "."
    env.run = lrun
    env.cd = lcd


def production():
    """
    Work on the production environment
    """
    env.hosts = [
        "159.203.191.135"
    ]  # list the ip addresses or domain names of your production boxes here
    env.port = 56565  # ssh port
    env.user = "root"  # remote user, see `env.run` if you don't log in as root

    env.compose_file = "docker-compose.prod.yml"
    env.project_dir = "/code/djangopackages"  # this is the project dir where your code lives on this machine

    # if you don't use key authentication, add your password here
    # env.password = "foobar"
    # if your machine has no bash installed, fall back to sh
    # env.shell = "/bin/sh -c"

    env.run = run  # if you don't log in as root, replace with 'env.run = sudo'
    env.cd = cd


def copy_secrets():
    """
    Copies secrets from local to remote.
    :return:
    """
    secrets = [
        ".env-production",
    ]

    for secret in secrets:
        remote_path = "/".join([env.project_dir, secret])
        print(
            blue(
                "Copying {secret} to {remote_path} on {host}".format(
                    secret=secret, remote_path=remote_path, host=env.host
                )
            )
        )
        put(secret, remote_path)


def rollback(commit="HEAD~1"):
    """
    Rollback to a previous commit and build the stack
    :param commit: Commit you want to roll back to. Default is the previous commit
    """
    with env.cd(env.project_dir):
        env.run(f"git checkout {commit}")

    deploy()


def backup():
    with env.cd(env.project_dir):
        # Manage Backups
        docker_compose("run django-a python manage.py clearsessions")
        docker_compose("run postgres backup")
        env.run("gzip /data/djangopackages/backups/*.sql")


def deploy():
    """
    Pulls the latest changes from main, rebuilt and restarts the stack
    """

    # lrun("git push origin main")
    # copy_secrets()
    with env.cd(env.project_dir):
        # Manage Backups
        # docker_compose("run django-a python manage.py clearsessions")

        # docker_compose("run postgres backup")
        # env.run("gzip /data/djangopackages/backups/*.sql")

        # Pull the latest code
        env.run("git pull origin main")

        # turn maintenance mode on
        # maintenance_mode_on("django-a")

        # Build our primary Docker image
        build_and_restart("django-a")
        time.sleep(10)

        # just to make sure they are on
        # docker_compose("start postgres")
        docker_compose("start redis")
        time.sleep(10)

        # Build our secondary Docker image
        build_and_restart("django-b")

        # collectstatic
        collectstatic("django-a")

        # turn maintenance mode off
        # maintenance_mode_off("django-a")


def build_and_restart(service):
    docker_compose(f"build {service}")
    docker_compose(f"create {service}")
    docker_compose(f"stop {service}")
    docker_compose(f"start {service}")


def collectstatic(service):
    docker_compose(f"exec {service} python manage.py collectstatic --no-input -v 1")


def maintenance_mode_on(service):
    docker_compose(f"exec {service} python manage.py maintenance_mode on")


def maintenance_mode_off(service):
    docker_compose(f"exec {service} python manage.py maintenance_mode off")


def purge_cache(service):
    docker_compose(
        f"exec {service} cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache"
    )


def docker_compose(command):
    """
    Run a docker-compose command
    :param command: Command you want to run
    """
    with env.cd(env.project_dir):
        return env.run(f"docker-compose -f {env.compose_file} {command}")
