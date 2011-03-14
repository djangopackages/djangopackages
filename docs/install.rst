Installation
============

.. parsed-literal::

    cd <installation-directory>
    virtualenv env-djangopackages
    source env-djangopackages/bin/activate
    git clone git://github.com/djangopackages/djangopackages.git djangopackages
    cd djangopackages
    pip install -r requirements/project.txt

In production add symlinks to the pinax and uni_form media directories::

    cd media
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/pinax/media/default/pinax/ pinax
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/uni_form/media/uni_form/ uni_form


Starting the development server
===============================

Change your local_settings.py file to point to prod.db then do::

    python manage.py runserver
