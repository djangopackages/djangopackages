FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore

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

RUN --mount=type=cache,target=/root/.cache,id=pip \
    python -m pip install --upgrade pip uv

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY requirements.txt /code/requirements.txt

RUN --mount=type=cache,target=/root/.cache,id=pip \
    uv pip install --system --requirement /code/requirements.txt

COPY . /code

RUN groupadd -r django \
    && useradd -r -g django django \
    && chown -R django /code

COPY ./dockerfiles/django/start-web.sh /start-web.sh
COPY ./dockerfiles/django/start-worker.sh /start-worker.sh

RUN sed -i 's/\r//' /start-web.sh \
    && chmod +x /start-web.sh \
    && chown django /start-web.sh

RUN sed -i 's/\r//' /start-worker.sh \
    && chmod +x /start-worker.sh \
    && chown django /start-worker.sh

WORKDIR /code

RUN DATABASE_URL=sqlite://:memory: REDIS_URL= python -m manage tailwind --skip-checks download_cli

RUN mkdir /data \
    && chown django.django /data

RUN mkdir /data/static \
    && chown django.django /data/static

RUN mkdir /data/media \
    && chown django.django /data/media

# Worker stage
FROM base AS worker

USER django
CMD ["/start-worker.sh"]

# Web stage (default)
FROM base AS web

USER django
CMD ["/start-web.sh"]
