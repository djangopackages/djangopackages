#!/bin/bash

set -e

if [ ! -f ".env.local" ]; then
    echo ".env.local created"
    cp .env.local.example .env.local
fi
