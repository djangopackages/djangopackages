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
from fabric.api import cd, env, lcd
from fabric.colors import blue
from fabric.operations import local as lrun
from fabric.operations import put, run
from rich import print


def local():
    """
    Work on the local environment
    """
    env.compose_file = "compose.yml"
    env.project_dir = "."
    env.run = lrun
    env.cd = lcd


def production():
    """
    Work on the production environment
    """
    env.hosts = [
        "165.22.184.193"
    ]  # list the ip addresses or domain names of your production boxes here
    env.user = "root"  # remote user, see `env.run` if you don't log in as root

    env.compose_file = "compose.prod.yml"
    env.project_dir = "/code/djangopackages"  # this is the project dir where your code lives on this machine
    env.run = run  # if you don't log in as root, replace with 'env.run = sudo'
    env.cd = cd


def setup():
    env.run("apt update")
    env.run(
        "apt install apt-transport-https ca-certificates curl software-properties-common"
    )
    env.run(
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg"
    )
    env.run(
        'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
    )
    env.run("apt update")
    env.run("apt-cache policy docker-ce")
    env.run("apt install docker-ce")
    env.run("systemctl status docker")
    env.run("systemctl enable docker.service")


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


def build_and_restart(service):
    docker_compose(f"build {service} --parallel --progress plain")
    docker_compose(f"create {service}")
    docker_compose(f"stop {service}")
    docker_compose(f"start {service}")


def clearsessions():
    """
    Clear old database sessions
    """

    with env.cd(env.project_dir):
        docker_compose("run django-a python -m manage clearsessions")


def cron():
    with env.cd(env.project_dir):
        docker_compose("run django-a python -m manage import_classifiers")
        docker_compose("run django-a python -m manage import_products")
        docker_compose("run django-a python -m manage import_releases")


def deploy(clearsessions: bool = False, stash: bool = False):
    """
    Pulls the latest changes from main, rebuilt and restarts the stack
    """

    # copy_secrets()

    with env.cd(env.project_dir):
        # Clear old database sessions
        if clearsessions:
            docker_compose("run django-a python -m manage clearsessions")

        # stash existing changes
        if stash:
            env.run("git stash")

        # Pull the latest code
        env.run("git pull origin main")

        # stash existing changes
        if stash:
            env.run("git stash pop")

        # turn maintenance mode on
        # maintenance_mode_on("django-a")

        # Build our primary Docker image
        build_and_restart("django-a")
        print("[yellow]waiting 10 seconds[/yellow]")
        time.sleep(10)

        # just to make sure they are on
        # docker_compose("start postgres")
        docker_compose("start redis")

        # print("[yellow]waiting 10 seconds[/yellow]")
        # time.sleep(10)

        # Build our secondary Docker image
        build_and_restart("django-b")

        # Restart django-q2
        docker_compose("stop django-q")
        docker_compose("start django-q")

        # collectstatic
        collectstatic("django-a")

        # turn maintenance mode off
        # maintenance_mode_off("django-a")


def collectstatic(service):
    docker_compose(f"exec {service} python -m manage collectstatic --no-input -v 1")


def maintenance_mode_on(service):
    docker_compose(f"exec {service} python -m manage maintenance_mode on")


def maintenance_mode_off(service):
    docker_compose(f"exec {service} python -m manage maintenance_mode off")


def purge_cache(service):
    docker_compose(
        f"exec {service} cli4 --delete purge_everything=true /zones/:djangopackages.org/purge_cache"
    )


def docker_compose(command, old=True):
    """
    Run a docker compose command
    :param command: Command you want to run
    """
    with env.cd(env.project_dir):
        return env.run(
            f"docker compose -f {env.compose_file} --profile utility {command}"
        )
