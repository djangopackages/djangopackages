from django.conf import settings
from health_check.views import HealthCheckView as BaseHealthCheckView
from redis.asyncio import Redis as RedisClient


class HealthCheckView(BaseHealthCheckView):
    """Health checks, with Redis included only when REDIS_URL is set.

    The checks are built per request, so they follow the current settings
    rather than whatever REDIS_URL was when urls.py was first imported.
    """

    def get_checks(self):
        checks = [
            "health_check.Cache",
            "health_check.Database",
        ]
        if settings.REDIS_URL:
            checks.append(
                (
                    "health_check.contrib.redis.Redis",
                    {
                        "client_factory": lambda: RedisClient.from_url(
                            settings.REDIS_URL
                        )
                    },
                )
            )
        self.checks = checks
        return super().get_checks()
