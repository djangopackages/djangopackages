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

Other problems
--------------

Don't give up!  Email audreyr@cartwheelweb.com with as much detail as you can include about the problem.
