FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE true
ENV PYTHONUNBUFFERED 1

# Install System dependencies
RUN set -x \
    && apt-get update \
    && apt-get install \
       -y \
       --no-install-recommends \
       --no-install-suggests \
       gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache,id=pip \
    pip install --upgrade pip pip-tools

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY ./requirements.txt /requirements.txt

RUN --mount=type=cache,target=/root/.cache,id=pip \
    pip install -r /requirements.txt

COPY ./dockerfiles/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh \
    && chmod +x /entrypoint.sh

COPY . /app

RUN groupadd -r django \
    && useradd -r -g django django \
    && chown -R django /app

COPY ./dockerfiles/django/start.sh /start.sh

RUN sed -i 's/\r//' /start.sh \
    && chmod +x /start.sh \
    && chown django /start.sh

WORKDIR /app

RUN mkdir /data \
    && chown django.django /data

RUN mkdir /data/static \
    && chown django.django /data/static

RUN mkdir /data/media \
    && chown django.django /data/media

ENTRYPOINT ["/entrypoint.sh"]
