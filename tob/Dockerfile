FROM python:3.10

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /usr/src/app

EXPOSE 80
# CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]