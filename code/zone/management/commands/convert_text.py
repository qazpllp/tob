import os
from pathlib import Path

from django.core.management import BaseCommand
from django.templatetags.static import static

import pdfkit
import markdown

from zone.models import Author, Story, Tag

class Command(BaseCommand):
    help = "Take text and convert it to various static files for better reading"

    # html, pdf, epub

    def add_arguments(self, parser):
        parser.add_argument(
            '--story_id', 
            help='Convert only a single story',
        )

    def handle(self, *args, **options):

        for s in Story.objects.all():
            if options['story_id'] and s.id != int(options['story_id']):
                continue

            # story_dir = os.path.join(static('zone/stories/'), str(s.id))
            story_dir = os.path.join('zone/static/zone/stories/', str(s.id))
            Path(story_dir).mkdir(parents=True, exist_ok=True)

            # pdf 
            options = {
                'page-size': 'Letter',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }

            # format newlines for html
            pdfkit.from_string(s.text.replace("\n", "<br>"), os.path.join(story_dir,str(s.id)+".pdf"), options=options)
            
            # html
            html = markdown.markdown(s.text)
            with open(os.path.join(story_dir,str(s.id)+".html"), 'w') as f:
                f.write(html)

            break