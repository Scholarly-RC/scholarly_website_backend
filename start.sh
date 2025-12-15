#!/bin/bash

# Wait for postgres
until pg_isready -h postgres -p 5432; do
  echo "Waiting for postgres..."
  sleep 1
done

python manage.py migrate

python manage.py qcluster &

gunicorn scholarly_website_backend.wsgi --bind 0.0.0.0:8000