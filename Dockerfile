# syntax=docker/dockerfile:1
FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# ENV DEBUG=0

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        wkhtmltopdf \
        pandoc \
        texlive \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy project code
COPY ./code /code/

# collect static files
RUN python manage.py collectstatic --noinput
