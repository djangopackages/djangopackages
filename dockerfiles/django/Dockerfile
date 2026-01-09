FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS release

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH /code
ENV PYTHONUNBUFFERED 1
ENV PYTHONWARNINGS ignore
ENV UV_LINK_MODE=copy

# Install System dependencies
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get -y --no-install-recommends install \
       curl \
       gcc \
       wget \
       build-essential

WORKDIR /code

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

COPY ./dockerfiles/django/entrypoint.sh /entrypoint.sh

RUN sed -i 's/\r//' /entrypoint.sh \
    && chmod +x /entrypoint.sh

COPY . .

RUN groupadd -r django \
    && useradd -r -g django django \
    && chown -R django /code

COPY ./dockerfiles/django/healthcheck-web.sh /code/healthcheck-web.sh
COPY ./dockerfiles/django/healthcheck-worker.sh /code/healthcheck-worker.sh
COPY ./dockerfiles/django/start-web.sh /code/start-web.sh
COPY ./dockerfiles/django/start-worker.sh /code/start-worker.sh

RUN DATABASE_URL=sqlite://:memory: REDIS_URL= uv run -m manage tailwind --skip-checks download_cli

RUN DATABASE_URL=sqlite://:memory: SECRET_KEY=build-key REDIS_URL= uv run -m manage tailwind --skip-checks build

RUN mkdir /data \
    && chown django.django /data

RUN mkdir /data/static \
    && chown django.django /data/static

RUN mkdir /data/media \
    && chown django.django /data/media

# ENTRYPOINT ["/entrypoint.sh"]

CMD ["/code/start-web.sh"]

# Worker stage
FROM release AS worker

HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/code/healthcheck-worker.sh"]

CMD ["/code/start-worker.sh"]

# Web stage (default)
FROM release AS web

HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD ["/code/healthcheck-web.sh"]

CMD ["/code/start-web.sh"]
