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
- ratings

Set SECRET_KEY to strong code, URL to url of site if being hosted for external use. An example is https://*.myapp.com where * is a literal asteriks, and adjust http(s) accordingly


## Deployment

This repository can either be ran using docker or wsgi.

Make a copy of `.env-example`, rename it to `.env` and adjust the values within appropriately.

### Docker

If using docker rename/copy `docker-compose-example.yml` to `docker-compose.yml`. You shouldn't really need to change anything in this file. You can, however, choose to remove the db image. This removes a Postgres database, and uses an SQLite instead

`docker-compose up`. then `docker-compose run web manage.py migrate` to mirgrate the database.

There should now be a functional but empty site.

### WSGI

This method is when not using docker. It is suitable for local development setups, or for deploying to site that launch using WSGI. Start by setting up the python environment `pipenv install -r requirements.txt`. Then `cd code/` to move into the working directory.

If running locally, `python manage.py runserver`, else set up the WSGI appropriately. Further down is an example of this using PythonAnywhere.

`python manage.py migrate` to mirgrate the database.

There should now be a functional but empty site

#### Set up site name

Go to `admin/sites/site`. Ensure a superuser has been previously made (`manage.py createsuperuser`). Alter the domain name to be the value used on the deployed site.
This is for sitemap and rss feed functionality.  

## To populate the database

Run the following commands in order

 - `python manage.py find_stories` to search TOB for stories. Populates titles, authors, e.t.c.
 - `python manage.py import_tags` to map tag slugs to a human-understandable phrase
 - `python manage.py get_stories` to download stories from TOB. Populates word count, text, and a cache file of the story
 - `python manage.py convert_text` to convert stored story text into a more consistent format outputted as pdf, html.

If the story/static files are already in place, run `python manage.py populate_db --use_static`. This version avoids downloading and converting stories, but uses those present (and queries the original website) to populate the database.

# Pythonanywhere

Include dotenv python package to make use of env variables (https://help.pythonanywhere.com/pages/environment-variables-for-web-apps). Run `pip install dotenv` within the pythonanywhere console, using the appropriate virual environment

set static path according to settings.py. By default this should be the url: `/static`, and the path can be anywhere relevant, e.g. `~/tob/code/static`. This setting is adjusted within the "website" tab.

To save on computation on the hosting device, it is recommended to set up a local version of the site. This site then runs the downloading and database-ing of the stories, which are then exported locally and imported onto the server.
Pre-populate the sqlite database locally (see above)by running `python manage.py populate_db --use_static` if not already done. Then run `python manage.py dumpdata dump.json`. Import this file somewhere into the pythonanywhere app, then import it `python manage.py loaddata /path/to/dump.json`.

Set up static files. Assuming a publically accessible google-drive location. In the PA console `pip install gdown`, then `gdown --id <file-id>`, to download it to the server. Then `unzip <file> -d code/zone/static/zone`. `manage.py collectstatic` to prepare all the stories into a quick static location. Finally delete the zip file

# comparison of hosting sites

## Heroku

Quite simple to set up. Variety of extentions. Need to use Amazon S3 + "Buckets" addon (£5), as well as a more sizable postgres database (£5)
Price ~ £10 a month + AWS S3 cost (around £0.01)
Has a good workflow for deployment. Can automatically deploy from git pushes.

## Pythonanywhere

By default uses the in-built Sqlite database. Free tier
£5 for extra compute power + enough space for files. £7 if wanting postgres database.
Needs a bit of manual CLI commands to get deployed. Not sure, but perhaps can use a script to deploy git pushes. More like running a VPS, or local machine

## Digital Ocean

### Droplet (Virtual machine)

£5 a month. Need to set up most things like site 

### App

Scalable. £5 a month to build python. Additional £5 for postgres database