# FAQ

## General

### How did Django Packages get started?

- In 2010 We realized there was no effective method for finding apps in the Django community.
- After launch we realized it might be good to use the same software system for other package sets.

### Are there any Case Studies?

- <http://pycon.blip.tv/file/4878766>
- <http://www.slideshare.net/pydanny/django-packages-a-case-study>

### How can I contribute?

Read the page on [contributions].

### How can I add a listing for a new Package or an entirely new Grid?

- Go the Home page, <https://www.djangopackages.org/>
- Click the appropriate button, where a package is a program and a grid is a category.

### What browsers does Django Packages support?

We do formal tests on Chrome, Safari and Firefox.

### How hard is it to add support for a new repo?

We've done a lot of work to make it as straightforward as possible. At PyCon 2011 we launched our formal [Repo Handler API].

## Supported Repo Hosting Services

Django Packages supports

The effort to support databases besides PostGreSQL was hampered for long time, all caused by a third party package we're not going to identify that caused grief in the use of fixtures. This was a significant issue in Django Packages, and used up a lot of development cycles.

We use a **Mock** system of creating sample data in our tests and for running a development version of the site. To create some development data, just run:

```shell
$ docker-compose run --rm django python manage.py load_dev_data
```

Alternatively, you can use `just`

```shell
$ just management-command load_dev_data
```

## Unsupported Repo Hosting Services

Django Packages supports GitHub and BitBucket. Here is some information about other repo hosting services.

## Troubleshooting

Don't give up!  Submit problems to <http://github.com/djangopackages/djangopackages/issues>. And don't forget:

1. Be polite! We are all volunteers.
2. Spend the time to learn GitHub markup

[contributions]: contributing.md
[faq]: faq
[repo handler api]: repo_handlers.md
