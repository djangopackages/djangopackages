============
Contributing
============

Setup
=====

Fork on github
--------------

Before you do anything else, login/signup on Github.com and fork Packaginator from https://github.com/cartwheelweb/packaginator.

Clone your package locally
--------------------------

If you have git-scm installed, you now clone your git repo using the following command-line argument::

    git clone git@github.com/cartwheelweb/packaginator.git

Installing Packaginator
-----------------------

Follow our detailed installation_ instructions. Please record any difficulties you have and share them with the Packaginator community via convore_ or our `issue tracker`_.

Issues!
=======

Packaginator has an extensive list of issues_. Pick an unassigned issue that you think you can accomplish, add comment that you are attempting to do it, and shortly your own personal label matching your github ID will be assigned to that issue.

Feel free to propose issues that aren't described!

Tips
----

#. **starter** labeled issues are deemed to be good low-hanging fruit for newcomers to the project, Django, or even Python.
#. **doc** labeled issues must only touch content in the docs folder.

Submitting patches as issues comments
-------------------------------------

While its handy to provide useful code snippets in an issue, it is better for you as a developer to submit pull requests. By submitting pull request your contribution to Packaginator will be recorded by Github. Which can only help getting your resume.

Pull upstream changes into your fork regularly
==================================================

Packaginator is advancing quickly. It is therefore critical that you pull upstream changes from master into your fork on a regular basis. Nothing is worse than putting in a days of hard work into a pull request only to have it rejected because it has diverged too far from master. 

To pull in upstream changes::

    git remote add packaginator git://github.com/cartwheelweb/packaginator.git
    git fetch packaginator

Check the log to be sure that you actually want the changes, before merging::

    git log ..packaginator/master

Then merge the changes that you fetched::

    git merge packaginator/master

For more info, see http://help.github.com/fork-a-repo/

How to get your Pull Request accepted
=====================================

We want your submission. But we also want to provide a stable experience for our users and the community. Follow these rules and you should succeed without a problem!

Run the tests!
--------------

Before you submit a pull request, please run the entire Packaginator test suite via::

    python manage.py test

The first thing the core committers will do is run this command. Any pull request that fails this test suite will be **rejected**.

If you add code/views you need to add tests!
--------------------------------------------

We've learned the hard way that code without tests is undependable. If your pull request reduces our test coverage because it lacks tests then it will be **rejected**.

For now, we use the Django Test framework (based on unittest) and Selenium.

Also, keep your tests as simple as possible. Complex tests end up requiring their own tests. We would rather see duplicated assertions across test methods then cunning utility methods that magically determine which assertions are needed at a particular stage. Remember: `Explicit is better than implicit`.

Don't mix code changes with whitespace cleanup
----------------------------------------------

If you change two lines of code and correct 200 lines of whitespace issues in a file the diff on that pull request is functionally unreadable and will be **rejected**. Whitespace cleanups need to be in their own pull request.

Keep your pull requests limited to a single issue
--------------------------------------------------

Packaginator pull requests should be as small/atomic as possible. Large, wide-sweeping changes in a pull request will be **rejected**, with comments to isolate the specific code in your pull request. Some examples:

#. If you are making spelling corrections in the docs, don't modify the settings.py file (pydanny_ is guilty of this mistake).
#. Adding a new `repo handler`_ must not touch the Package model or its methods.
#. If you are adding a new view don't '*cleanup*' unrelated views. That cleanup belongs in another pull request.
#. Changing permissions on a file should be in its own pull request with explicit reasons why.

Follow pep-8 and keep your code simple!
---------------------------------------

Memorize the Zen of Python::

    >>> python -c 'import this'

Please keep your code as clean and straightforward as possible. When we see more than one or two functions/methods starting with `_my_special_function` or things like `__builtins__.object = str` we start to get worried. Rather than try and figure out your brilliant work we'll just **reject** it and send along a request for simplification.

Furthermore, the pixel shortage is over. We want to see:

* `package` instead of `pkg`
* `grid` instead of `g`
* `my_function_that_does_things` instead of `mftdt`

Test any css/layout changes in multiple browsers
------------------------------------------------

Any css/layout changes need to be tested in Chrome, Safari, Firefox, IE8, and IE9 across Mac, Linux, and Windows. If it fails on any of those browsers your pull request will be **rejected** with a note explaining which browsers are not working.

.. _installation: install.html
.. _issue tracker: https://github.com/cartwheelweb/packaginator/issues
.. _issues: https://github.com/cartwheelweb/packaginator/issues
.. _repo handler: repo_handlers.html
.. _convore: http://convore.com/packaginator
.. _pydanny: http://pydanny.com