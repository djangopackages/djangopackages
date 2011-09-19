=============
Introduction
=============

Ever want to know which is the most popular or well supported Python httplib replacement, web framework, or api tool? Packaginator solves that problem for you! Packaginator allows you to easily identify good apps, frameworks, and packages.

Packaginator stores information on fetched packages and provides easy comparison tools for them. Public APIs include PyPI, Github, BitBucket, Launchpad, and perhaps soon SourceForge and Google Project Hosting.

The Site
--------

A current example is live: http://www.djangopackages.com

Grids!
~~~~~~

Grids let you compare packages. A grid comes with default comparison items and you can add features to get a more specific. We think comparison grids are an improvement over traditional tagging system because specificity helps make informed decisions.

Categories of Packages
~~~~~~~~~~~~~~~~~~~~~~

The fixtures provide four categories: apps, frameworks, projects, and utilities.

What repo sites are supported?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 * Github
 * Bitbucket
 * Launchpad.

Google Project Hosting and Sourceforge are not fully supported!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not yet!

The progenitor of Packaginator, Django Packages was cooked up during Django Dash 2010. We wanted to keep the scope of our work reasonable. We'll try to include more sites in the future. Here are some details:

 * Sourceforge needs needs to repair their API and then we can play.
 * Google's lack of a formal API leaves us the option of screen-scraping their content. We're not excited about introducing that sort of brittle activity into Packaginater.
