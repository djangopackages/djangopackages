============
Installation
============

These instructions install Django Packages on your computer, using Docker.

If you run into problems, see the Troubleshooting section.

Set Up Docker Tools
===================

If you don't have them installed yet, install Docker_ and docker-compose_.

Grab a Local Copy of the Project
--------------------------------

Clone the Django Packages project using git:

.. code-block:: bash

    git clone git@github.com:<your-github-username>/djangopackages.git
    cd djangopackages

Set Up Your Development Environment
-----------------------------------

In order to run the project, you first need to add a file called ``.env.local``.
The file holds all the configurable settings and secrets to run properly.

There's an example file available. To get started, copy the file:

.. code-block:: bash

    cp .env.local.example .env.local

Build the Docker Containers
---------------------------

Now build the project using docker-compose:

.. code-block:: bash

    docker-compose -f dev.yml build

Run the Project
---------------

To start the project, run:

.. code-block:: bash

    docker-compose -f dev.yml up

Then point your browser to http://localhost:8000 and start hacking!

Create a Local Django Superuser
-------------------------------

Now, you'll give yourself an admin account on the locally-running version of Django Packages

Create a Django superuser for yourself, replacing joe with your username/email:

.. code-block:: bash

    docker-compose -f dev.yml run django python manage.py createsuperuser --username=joe --email=joe@example.com

And then login into the admin interface (/admin/) and create a profile for your user filling all the fields with any data.

.. _Docker: https://docs.docker.com/install/
.. _docker-compose: https://docs.docker.com/compose/install/
