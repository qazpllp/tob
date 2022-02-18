from pathlib import Path
import shutil

from django.core.management import BaseCommand
from django.templatetags.static import static
from django.core.files import File
from django.conf import settings
from zone.models import Story


class Command(BaseCommand):
	help = 'Quick and dirty add text files to files model field'

	def add_arguments(self, parser):
		parser.add_argument('--forced', action="store_true", help="Overwrite already stored data. Equivalent to all the other optional arguments together")
		parser.add_argument('--forced_download', action="store_true", help="Re-download stories")
		parser.add_argument('--forced_textify', action="store_true", help="Overwrite text data")
		parser.add_argument('--forced_wordcount', action="store_true", help="Overwrite word count")
		parser.add_argument('--story_id', help="Download a particular story (if already known about in database)")
		parser.add_argument('--no_cache', action="store_true", help="Do not use cache, use static files only")
	
	def handle(self, *args, **options):

		stories = Story.objects.all()
		for s in stories:
			print(f'{s}')
			path = Path(f'zone/static/zone/stories/{s.id}/{s.id}.md')

			try:
				with path.open(mode='r') as f:
					s.text = File(f, name=path.name)
					s.save()
			except:
				pass
