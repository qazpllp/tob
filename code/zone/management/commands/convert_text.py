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
		parser.add_argument(
			'--forced', 
			action="store_true", 
			help="Overwrite already stored data")

	def handle(self, *args, **options):
		if options['story_id']:
			stories = [Story.objects.get(id=options['story_id'])]
			options['forced'] = True
		else:
			stories = Story.objects.all()

		for s in stories:
			if s.text == '':
				print(f'{s} has no text to convert')
				continue

			story_dir = os.path.join('zone/static/zone/stories/', str(s.id))
			Path(story_dir).mkdir(parents=True, exist_ok=True)

			# markdown
			md_name = os.path.join(story_dir,str(s.id)+".md")
			if not os.path.exists(md_name) or (os.path.exists(md_name) and options['forced']):
				print(f"Converting {s} to markdown")

				with open(md_name, 'w') as f:
					f.write(s.text)
			
			# html
			html_name = os.path.join(story_dir,str(s.id)+".html")
			if not os.path.exists(html_name) or (os.path.exists(html_name) and options['forced']):
				print(f"Converting {s} to html")

				html = markdown.markdown(s.text)
				with open(html_name, 'w') as f:
					# Write some styling in the head
					f.write('<!DOCTYPE html>\n<html lang="en">\n')
					f.write('<head>\n')
					f.write('\t<meta charset="utf-8">\n')
					f.write(f'\t<title>{s.title}</title>\n')
					with open('zone/static/zone/headstyle.html', 'r') as headstyle:
						f.write(headstyle.read())
					f.write('\n</head>\n')
					f.write('<body>\n')
					f.write(html)
					f.write('\n</body>\n</html>')

			# pdf 
			pdf_name = os.path.join(story_dir,str(s.id)+".pdf")
			if not os.path.exists(pdf_name) or (os.path.exists(pdf_name) and options['forced']):
				print(f"Converting {s} to pdf")

				opts = {
					'page-size': 'Letter',
					'margin-top': '0.75in',
					'margin-right': '0.75in',
					'margin-bottom': '0.75in',
					'margin-left': '0.75in',
					'encoding': "UTF-8",
					'enable-local-file-access': None,
				}

				# format newlines for html
				with open(html_name, 'r') as f:
					pdfkit.from_file(f, pdf_name, options=opts)
				# pdfkit.from_string(s.text, pdf_name, options=opts)
