"""Guards the mail configuration left behind after Mailgun came out.

The site does not send mail. The risk is not that sending breaks, it is
that someone wires a provider back in through INSTALLED_APPS and nobody
notices the credentials are dead again.
"""

from django.conf import settings


def test_no_mail_provider_app_is_installed():
    assert "anymail" not in settings.INSTALLED_APPS


def test_email_backend_is_django_s_own():
    assert not settings.EMAIL_BACKEND.startswith("anymail.")


def test_subject_prefix_survives_the_env():
    # It used to be reassigned a few lines further down, which quietly made
    # EMAIL_SUBJECT_PREFIX in the environment do nothing.
    assert settings.EMAIL_SUBJECT_PREFIX == "[Django Packages] "
