from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django_q.models import Schedule
from django_q.tasks import schedule

TIMEOUT = 20 * 60 * 60  # 20 hours


class Command(BaseCommand):
    help = "Add Scheduled Jobs to django-q cluster"

    def handle(self, *args, **options):
        searchv3_build_tasks_name = "Build Search V3"
        package_updater_tasks_name = "Update All Packages from GitHub"
        pypi_updater = "Update All Packages from PyPI"

        success_message = "Created '{tasks_name}' scheduled task successfully"
        integrity_error_message = "'{tasks_name}' scheduled task already exists"

        try:
            schedule(
                "django.core.management.call_command",
                "searchv3_build",
                name=searchv3_build_tasks_name,
                schedule_type=Schedule.CRON,
                cron="12 23 * * *",
                q_options={
                    "timeout": TIMEOUT,
                    "max_attempts": 1,
                },
            )
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING(
                    integrity_error_message.format(tasks_name=searchv3_build_tasks_name)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    success_message.format(tasks_name=searchv3_build_tasks_name)
                )
            )

        try:
            schedule(
                "django.core.management.call_command",
                "package_updater",
                name=package_updater_tasks_name,
                schedule_type=Schedule.CRON,
                cron="36 17 * * *",
                q_options={
                    "timeout": TIMEOUT,
                    "max_attempts": 1,
                },
            )
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING(
                    integrity_error_message.format(
                        tasks_name=package_updater_tasks_name
                    )
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    success_message.format(tasks_name=package_updater_tasks_name)
                )
            )

        try:
            schedule(
                "django.core.management.call_command",
                "pypi_updater",
                name=pypi_updater,
                schedule_type=Schedule.CRON,
                cron="48 21 * * *",
                q_options={
                    "timeout": TIMEOUT,
                    "max_attempts": 1,
                },
            )
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING(
                    integrity_error_message.format(tasks_name=pypi_updater)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(success_message.format(tasks_name=pypi_updater))
            )
