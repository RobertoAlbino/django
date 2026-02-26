#!/bin/sh
set -e

python manage.py migrate --run-syncdb

exec "$@"
