#!/bin/sh

uv run -m manage migrate --noinput

uv run -m manage server dev
