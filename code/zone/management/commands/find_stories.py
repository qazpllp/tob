from urllib import request, error
import datetime
import os
from pathlib import Path
from django.core.management import BaseCommand
from bs4 import BeautifulSoup

from zone.models import Author, Story, Tag


class Command(BaseCommand):
    help = 'Find stories/authors/tags on TOB. Imports info to database'

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         '--create-only', 
    #         action="store_true",
    #         help='Does not update if already exists',
    #     )
    #     # parser.add_argument('limit_number', help='Limit the number of searched files')
    
    def handle(self, *args, **options):
        urlYearBase = "https://overflowingbra.com/ding.htm?dates="
        htmls = []
        # stories = []

        # Find available stories by searching by year
        for year in range(1998, datetime.datetime.now().year):
            
            # store pages for later use
            html_path = 'zone/cache/zone/original/'
            Path(html_path).mkdir(parents=True, exist_ok=True)
            filename = os.path.join(html_path, str(year) + ".html")

            if not os.path.exists(filename):
                url = urlYearBase + str(year)
                try:
                    obj = request.urlopen(url)
                except error.HTTPError as e:
                    print('Error code: ', e.code)
                except error.URLError as e:
                    print('Reason: ', e.reason)
                text = obj.read()
                htmls.append(text)
                with open(filename, 'wb') as f:
                    f.write(text)
            else:
                print(f"Using cache for year {year}")
                with open(filename, 'rb') as f:
                    htmls.append(f.read())

        for html_doc in htmls:
            soup = BeautifulSoup(html_doc, 'html.parser')

            for i, story in enumerate(soup.find_all("div", class_="storybox")):
                author = story.find("div", class_="author").a.contents[0]
                title = story.find("div", class_="storytitle").a.contents[0]
                
                try:
                    date = story.find("div", class_="submitdate").contents[0]
                    
                    # remove text on the day (e.g. 3rd)
                    day = date.split(',')
                    day[0] = ''.join([i for i in day[0] if i.isdigit()])
                    date = ''.join(day)

                    date = datetime.datetime.strptime(date, '%d %b %y')
                except:
                    date = datetime.datetime(1970, 1, 1)
                
                try:
                    summarys = story.find("div", class_="summary").contents
                    summary = ' '.join(x.text for x in summarys)
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

                # else:
                story, created_s = Story.objects.update_or_create(
                    id = storyId,
                    pub_date = date,
                    title = title,
                    summary = summary,
                    author = author,
                    # The following values may change when accessing the same story at different times
                    defaults = {
                        'words': 0,
                        'downloads': downloads,
                    }
                )

                # story must be saved before assigning many-to-many tags field
                if created_s:
                    for t in tags_found:
                        story.tags.add(t)

                if created_a:
                    print(f"Creating author {author}")
                if created_s:
                    print(f"Creating Story {title}")
