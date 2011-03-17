===============
Troubleshooting
===============

No module named abc
-------------------

If you're getting something like "ImportError: No module named abc", you probably don't have all the required packages installed.  Try::

    pip install -r requirements/project.txt

ImportError related to launchpad.py
-----------------------------------

Sometimes this shows up as "Caught ImportError while rendering: cannot import name ScalarValue".

You're having Launchpad/bzr installation problems.  Most likely cause is your C compiler.  On Windows, make sure you have MinGW installed as per the installation instructions.  On Linux, make sure you have the python-dev and gcc packages.

I can't get it to work in buildout!
-----------------------------------

We have a very successful installation story for development and production hosting using virtualenv. While buildout is a wonderful tool we simply don't want to spend the time supporting two installation methods. Therefore:

* Don't do it.
* We won't accept pull requests for it.

Other problems
--------------

Don't give up!  Join us at http://convore.com/packaginator and ask your questions there. Some quick rules of thumb to optimize the help from the Packaginator community:

#. Be polite! We are all volunteers.
#. Don't paste huge chunks of code into convore blocks. Use a code pasting service like http://dpaste.com or http://djaste.de.
