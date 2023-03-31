FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE true
ENV PYTHONUNBUFFERED 1

RUN --mount=type=cache,target=/root/.cache,id=pip \
    pip install --upgrade pip pip-tools

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY ./requirements.txt /requirements.txt

RUN --mount=type=cache,target=/root/.cache,id=pip \
    pip install -r /requirements.txt

COPY ./dockerfiles/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

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
