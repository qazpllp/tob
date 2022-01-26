# syntax=docker/dockerfile:1
FROM python:3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy project code
COPY ./code /code/

# collect static files
RUN python manage.py collectstatic --noinput

# add and run as non-root user
# RUN adduser -D userfoo
# USER userfoo

# run gunicorn
# CMD gunicorn tob.wsgi:application --bind 0.0.0.0:$PORT