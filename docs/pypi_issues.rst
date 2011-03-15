PyPI Issues
===========

You may ask why the PyPI code is a bit odd in places. PyPI is an organically grown project and uses its own custom designed framework rather than the dominant frameworks that existed during its inception (these being Pylons, Django, TurboGears, and web.py). Because of this you get things like the API having in its package_releases() method an explicit license field that has been replaced by the less explicit list column in the very generic classifiers field. So we have to parse things like this to get a particular package's license::

    ['Development Status :: 5 - Production/Stable', 'Environment :: Web Environment',
    'Framework :: Django', 'Intended Audience :: Developers', 'License :: OSI Approved
    :: BSD License', 'Operating System :: OS Independent', 'Programming Language ::
    Python', 'Topic :: Internet :: WWW/HTTP', 'Topic :: Internet :: WWW/HTTP ::
    Dynamic Content', 'Topic :: Internet :: WWW/HTTP :: WSGI', 'Topic :: Software
    Development :: Libraries :: Application Frameworks', 'Topic :: Software
    Development :: Libraries :: Python Modules']

The specification is here and this part of it just makes no sense to me::

    http://docs.python.org/distutils/setupscript.html#additional-meta-data