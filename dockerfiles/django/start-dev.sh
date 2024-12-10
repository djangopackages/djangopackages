#!/bin/sh

# python -m manage tailwind --skip-checks build

python -m manage migrate --noinput

python -m manage runserver --skip-checks 0.0.0.0:8000
