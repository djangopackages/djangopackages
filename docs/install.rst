============
Installation
============

Do everything listed in this section to get your site up and running locally.  If you run into problems, see the Troubleshooting section.

Pre-requisites
==============

You need to install Docker_ and docker-compose_.

Main instructions
=================

These instructions install Django Packages on your computer, using Docker.

Git clone the project
---------------------

Clone the Django Packages project using git:

.. code-block:: bash

    git clone git@github.com:djangopackages/djangopackages.git
    cd djangopackages

Set up the development environment
----------------------------------

In order to run the project, you first need to add a file called ``.env.local``.
The file holds all the configurable settings and secrets to run properly.

There's an example file available. To get started, copy the file:

.. code-block:: bash

    cp .env.local.example .env.local

Build Docker container
----------------------

Now build the project using docker-compose:

.. code-block:: bash

    docker-compose -f dev.yml build

Running the project
-------------------

To start the project, run:

.. code-block:: bash

    docker-compose -f dev.yml up

Then point your browser to http://localhost:8000 and start hacking!

Give yourself an admin account on the site
------------------------------------------

Create a Django superuser for yourself, replacing joe with your username/email:

.. code-block:: bash

    docker-compose -f dev.yml run django python manage.py createsuperuser --username=joe --email=joe@example.com

And then login into the admin interface (/admin/) and create a profile for your user filling all the fields with any data.

.. _Docker: https://docs.docker.com/install/
.. _docker-compose: https://docs.docker.com/compose/install/
