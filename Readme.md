# TOB

Code for a re-written, unofficial clone of TOB.

if theres anissue with the database getting out of sync.
Move the app 'zone' away from the folder.
Remove traces of it in settings and url in 'tob'
Delete database info
run manage.py migrate
Add files and info back in
run migrate again

Todo:
- weigh search vector?
- Serve static files for deployment (https://docs.djangoproject.com/en/3.2/howto/static-files/#serving-files-uploaded-by-a-user-during-development)
- Rss feed?

Set SECRET_KEY to strong code, URL to url of site if being hosted for external use. An example is https://*.myapp.com where * is a literal asteriks, and adjust http(s) accordingly

## Heroku

This repo can be easily and quickly hosted using Heroku. 
Contains a heroku.yml file that sets up a lot of the requirements. Should be as simple as git-pushing this repo/branch to the heroku app.

## missing static files
https://help.heroku.com/K1PPS2WM/why-are-my-file-uploads-missing-deleted
>The Heroku filesystem is ephemeral - that means that any changes to the filesystem whilst the dyno is running only last until that dyno is shut down or restarted. Each dyno boots with a clean copy of the filesystem from the most recent deploy. This is similar to how many container based systems, such as Docker, operate.

In addition, under normal operations dynos will restart every day in a process known as "Cycling".

These two facts mean that the filesystem on Heroku is not suitable for persistent storage of data. In cases where you need to store data we recommend using a database addon such as Postgres (for data) or a dedicated file storage service such as AWS S3 (for static files). If you don't want to set up an account with AWS to create an S3 bucket we also have addons here that handle storage and processing of static assets https://elements.heroku.com/addons


# Docker buildkit
Uses buildkit to have branching builds depending on the target storage rules. If it has ephemiral storage (e.g. Heroku), then it fetches a pre-configured set of stories.
If storage is more permanent then can use the manage.py commands to download and tranform the stories
Set environment variable DOCKER_BUILDKIT=1 

e.g.
```
$ DOCKER_BUILDKIT=1 docker build .
```

Needs docker >= 18.09

## Deployment

Two options are configured within this repo. They are by using docker, or Heroku.
They build the docker image, use a PostgreSQL database.

Populate database with `python manage.py migrate`

### Local/Docker

Copy/rename `docker-compose-example.yml` to `docker-compose.yml`. Edit the variabled accordingly (e.g. `URL`, `CSRF_URL` to LAN IP if accessible over LAN)

``` bash
docker-compose up
```

### Heroku

git push heroku stories:master

This pushes the stories branch to heroku for building, which must take a master/main branch name. The use of the stories branch is that it contains all the stories in pdf,html form already. This prevents the requirement of using an extra paid extention for storing static files (e.g. AWS S3). It is useful so the deployment is entirely free, but prevents the future possibility of dynamic file uploads and user-specified file changes.

Add environment variables `URL` and `CSRF_URL`