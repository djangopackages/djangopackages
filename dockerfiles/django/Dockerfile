FROM python:3.11-slim-bookworm

ENV PATH /venv/bin:/bin:/usr/bin:/usr/sbin:/usr/local/bin
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH /code
ENV PYTHONUNBUFFERED 1
ENV PYTHONWARNINGS ignore

# Install System dependencies
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get -y --no-install-recommends install \
       gcc \
       build-essential

RUN --mount=type=cache,target=/root/.cache,id=pip \
    python -m pip install --upgrade pip uv

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY requirements.txt /code/requirements.txt

RUN uv venv /venv

RUN --mount=type=cache,target=/root/.cache,id=pip \
    . /venv/bin/activate && \
    uv pip install --requirement /code/requirements.txt

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
