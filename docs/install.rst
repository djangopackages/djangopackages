============
Installation
============

These instructions install Django Packages on your computer, using Docker.

If you run into problems, see the Troubleshooting section.

Set up Tooling
==============

You'll want to make sure your local environment is ready by installing the following tools.

Docker
------

If you don't have them installed yet, install Docker_ and docker-compose_.

just
----

We use the command runner just_. Install instructions are available on the just_ GitHub page. 

pipx
----

We use `pipx` to install various linters and formatters so you'll need to install it. 

Install instructions are available on the here on pipx_.

Formatters, Linters, and other miscellanea
------------------------------------------

You'll want to install the various formatters, and linters using the following `pipx` command. 

To do this, run:

.. code-block:: bash
    just pipx-install

Grab a Local Copy of the Project
--------------------------------

`Fork <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_ the Django Packages project 

Clone the Django Packages project using git:

.. code-block:: bash

    git clone git@github.com:<your-github-username>/djangopackages.git
    cd djangopackages

Set Up Your Development Environment
-----------------------------------

In order to run the project, you'll need to run the following command:

.. code-block:: bash
    just setup

Add A GitHub API Token
----------------------

Get a `GitHub API token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token>`_ and set the ``GITHUB_TOKEN`` variable in ``.env.local``
to this value.  This is used by the GitHub repo handler for fetching repo
metadata, and required for certain tests.

Build the Docker Containers
---------------------------

Now build the project using docker-compose:

.. code-block:: bash

    docker-compose build

Run the Project
---------------

To start the project, run:

.. code-block:: bash

    docker-compose up

Then point your browser to http://localhost:8000 and start hacking!

Create a Local Django Superuser
-------------------------------

Now, you'll give yourself an admin account on the locally-running version of Django Packages

Create a Django superuser for yourself, replacing joe with your username/email:

.. code-block:: bash

    docker-compose run django python manage.py createsuperuser --username=joe --email=joe@example.com

And then login into the admin interface (/admin/) and create a profile for your user filling all the fields with any data.

.. _Docker: https://docs.docker.com/install/
.. _docker-compose: https://docs.docker.com/compose/install/
.. _just: https://github.com/casey/just
.. _pipx: https://pypa.github.io/pipx/