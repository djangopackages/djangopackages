=============
Introduction
=============

Packaginator solves the problem in the Python community of being able to easily identify good apps, frameworks, and packages. Ever want to know which is the most popular or well supported Python httplib replacement, web framework, or api tool? Packaginator solves that problem for you! 

It does this by storing information on packages fetched from public APIs provided by PyPI, Github, BitBucket, Launchpad, and SourceForge, and then provides extremely useful comparison tools for them.

The Site
--------

The most current example is live and functional at http://www.djangopackages.com.

Grids!
~~~~~~

Grids let you compare packages to each other. A grid comes with a number of default items compared, but you can add more features in order to get a more specific comparison.

We think grids are a gigantic improvement over the traditional tagging system, because we think that grids give us a lot more specificity.

Categories of Packages
~~~~~~~~~~~~~~~~~~~~~~

The fixtures provide four categories: apps, frameworks, projects, and utilities.

Google Project Hosting and Sourceforge are not fully supported!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not yet. 

The progenitor of Packaginator, Django Packages was cooked up during Django Dash 2010. We wanted to keep the scope of our work reasonable. We'll try and include those sites in the future. We also want to include other package repo systems over time. As for what we support:

 * Packaginator does support Github and Bitbucket and Launchpad.
 * Sourceforge needs some tweaking but is otherwise it is done.
 * Google Project Hosting may not happen because of a lack of a formal API and not much desire to screen scrape their arcane browser interface.