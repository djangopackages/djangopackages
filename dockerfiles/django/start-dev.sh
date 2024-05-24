#!/bin/sh
python -m manage migrate --noinput

python -m manage runserver 0.0.0.0:8000
