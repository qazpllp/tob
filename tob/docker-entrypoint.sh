#!/bin/bash

# Wait for database
until nc -z timeline-db 5432; do echo Waiting for PostgreSQL; sleep 1; done

python manage.py migrate                  # Apply database migrations
python manage.py collectstatic --noinput  # Collect static files
python manage.py runserver 0.0.0.0:80