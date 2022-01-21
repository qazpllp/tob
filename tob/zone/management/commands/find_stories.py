from urllib import request, error
import datetime
import ast
from django.core.management import BaseCommand
from bs4 import BeautifulSoup

from zone.models import Author, Story, Tag


class Command(BaseCommand):
    help = 'Find stories/authors/tags on TOB. Imports info to database'

    def add_arguments(self, parser):
        parser.add_argument('--create-only', help='Does not update if already exists')
        # parser.add_argument('limit_number', help='Limit the number of searched files')
    
    def handle(self, *args, **options):
        urlYearBase = "https://overflowingbra.com/ding.htm?dates="
        htmls = []
        # stories = []

        # Find available stories by searching by year
        for year in range(2000, datetime.datetime.now().year):
            url = urlYearBase + str(year)
            try:
                obj = request.urlopen(url)
            except error.HTTPError as e:
                print('Error code: ', e.code)
            except error.URLError as e:
                print('Reason: ', e.reason)
            htmls.append(obj.read())
            break

        for html_doc in htmls:
            soup = BeautifulSoup(html_doc, 'html.parser')

            for i, story in enumerate(soup.find_all("div", class_="storybox")):
                author = story.find("div", class_="author").a.contents[0]
                title = story.find("div", class_="storytitle").a.contents[0]
                
                try:
                    date = story.find("div", class_="submitdate").contents[0]
                    date = datetime.datetime.strptime(date, '%dth, %b %y')
                except:
                    date = datetime.datetime(1970, 1, 1)
                
                try:
                    summary = story.find("div", class_="summary").contents[0]
                except:
                    summary = ""
                
                try:
                    tags = story.find("div", class_="storycodes").contents[0].split()
                except:
                    tags = []
                downloads = int(story.find("div", class_="downloads").contents[0].split()[0])
                authorId = story.find("div", class_="author").a["href"].split("=")[1]
                storyId = story.find("div", class_="storytitle").a["href"].split("=")[1]


                author, created_a = Author.objects.get_or_create(
                    id = authorId,
                    name = author,
                )

                tags_found = []
                for t in tags:
                    tag, created_t = Tag.objects.get_or_create(
                        slug = t
                    )
                    tags_found.append(tag)

                if options['create-only']:
                    story = Story.objects.create(
                        id = storyId,
                        title = title,
                        pub_date = date,
                        summary = summary,
                        author = author,
                        # The following values may change when accessing the same story at different times
                        defaults = {
                            'words': 0,
                            'downloads': downloads,
                        }
                    )
                    created_s = True

                else:
                    story, created_s = Story.objects.update_or_create(
                        id = storyId,
                        title = title,
                        pub_date = date,
                        summary = summary,
                        author = author,
                        # The following values may change when accessing the same story at different times
                        defaults = {
                            'words': 0,
                            'downloads': downloads,
                        }
                    )

                # story must be saved before assigning many-to-many tags field
                for t in tags_found:
                    story.tags.add(t)

                if created_a:
                    print(f"Creating author {author}")
                if created_s:
                    print(f"Creating Story {title}")
