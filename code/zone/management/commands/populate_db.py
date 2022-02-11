import csv
from urllib import request, error
import datetime
import os
from pathlib import Path
import shutil
import glob
import codecs
from io import StringIO
import re

from django.core.management import BaseCommand

from bs4 import BeautifulSoup
import pdfminer
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

import pypandoc
from markdownify import markdownify

from zone.models import Author, Story, Tag

class Command(BaseCommand):
	help = 'import a csv of the generated site tag information'

	def add_arguments(self, parser):
		parser.add_argument('--forced', action="store_true", help="Overwrite already stored data. Equivalent to all the other optional arguments together")
		parser.add_argument('--forced_download', action="store_true", help="Re-download stories")
		parser.add_argument('--forced_textify', action="store_true", help="Overwrite text data")
		parser.add_argument('--forced_wordcount', action="store_true", help="Overwrite word count")
		parser.add_argument('--use_static', action="store_true", help="Use the static file stories to get word information. Avoids downloading. Doesn't use cache.")
		parser.add_argument('--story_id', help="Download a particular story (if already known about in database)")


	def handle(self, *args, **options):
		# self.find_stories(*args, **options)
		# self.import_tags(*args, **options)

		# handle arguments
		if options['story_id']:
			stories = [Story.objects.get(id=options['story_id'])]
			options['forced'] = True
		else:
			stories = Story.objects.all()
		if options['forced']:
			options['forced_download'] = options['forced_textify'] = options['forced_wordcount'] = True

		# iterate over stories
		raw_loc = 'zone/cache/zone/stories_raw/'
		Path(raw_loc).mkdir(parents=True, exist_ok=True)
		for s in stories:
			if not options['use_static']:
				self.download_story(s, *args, **options)
				self.story_to_markdown(s, *args, **options)
			self.get_wordcount(s)

	def find_stories(self, *args, **options):
		"""
		Find stories/authors/tags on TOB. Imports info to database
		"""
		urlYearBase = "https://overflowingbra.com/ding.htm?dates="
		htmls = []

		# Find available stories by searching by year
		for year in range(1998, datetime.datetime.now().year + 1):
			
			# store pages for later use
			html_path = 'zone/cache/zone/original/'
			Path(html_path).mkdir(parents=True, exist_ok=True)
			filename = os.path.join(html_path, str(year) + ".html")

			# Try to use cache if html file found in cache, and not current year
			if not os.path.exists(filename) or year == datetime.datetime.now().year:
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

	def import_tags(self, *args, **options):
		"""
		import a csv of the generated site tag information, and saves tags to model
		"""
		with open('zone/static/zone/tags_mapping.txt') as f:
			reader = csv.reader(f)
			for row in reader:
				tag, created_t = Tag.objects.update_or_create(
					slug = row[0],
					description = row[1],
					defaults = {'category': row[2]}
				)

	def download_story(self, story: Story, *args, **options):
		"""
		Download story from TOB
		"""
		baseUrl = "https://overflowingbra.com/download.php?StoryID="

		raw_loc = 'zone/cache/zone/stories_raw/'
		Path(raw_loc).mkdir(parents=True, exist_ok=True)

		# file of interest
		folderName=os.path.join(raw_loc, str(story.id))
		url = baseUrl + str(story.id)

		# Download story as necessary
		if not os.path.exists(folderName) or (os.path.exists(folderName) and options['forced_download']):
			print(f"Downloading {story}")
			try:
				tempname,_ = request.urlretrieve(url, "zone/cache/zone/temp.zip")
			except:
				print(f"Failed to download {story}")
			try:
				shutil.unpack_archive(tempname, folderName)
			except:
				print(f"Failed to extract {story}")

			# clear up tempfile after use
			os.remove(tempname)
		else:
			print(f"Story {story} already exists on disk")

	def story_to_markdown(self, story: Story, *args, **options):
		"""
		Extract text from downloaded story (in cache), into markdown format, and save
		"""
		raw_loc = 'zone/cache/zone/stories_raw/'
		Path(raw_loc).mkdir(parents=True, exist_ok=True)
		# file of interest
		folderName=os.path.join(raw_loc, str(story.id))

		# Textify story as necessary (convert into markdown)
		text = self.get_story_text(story)
		if text == "" or (not text == "" and options['forced_textify']):
			print(f"Textifying {story}")
			handled = False

			# Various strings (key) to replace with (value)
			replace_dict = {
				'\00': ' ', # Null Character
				'\xa0': ' ', # remove nbsp character
			}

			# extentions that can and will be converted. Order first as highest priority. Try to order in ease of conversion to markdown, and that has relevant styling (headings, e.t.c.)
			exts = ['html', 'htm', 'doc', 'docx', 'odt', 'pdf', 'rtf', 'txt']

			# loop through file extentions in decreasing priority of conversion
			for ext in exts:
				# Find all files of this extention for this story
				filenames = []
				for filename in glob.iglob(folderName + '/**/*.' + ext, recursive=True):
					filenames.append(filename)
				if not filenames or handled:
					continue

				# text could come from multiple files, if multiple files have the same extention
				text = []					
				for filename in filenames:

					# html
					ext_html = ['html', 'htm']
					if ext in ext_html:
						t, handled = self.html2md(filename)
						text.append(t)


					# pandoc
					exts_pandoc = ['doc', 'docx', 'odt']
					if ext in exts_pandoc:
						extra_args=['--atx-headers']
						try:
							t = pypandoc.convert_file(filename, 'md', 
								extra_args=extra_args)
							text.append(t)
							handled = True
						except:
							pass

					# pdf
					ext_pdf = ['pdf']
					if ext in ext_pdf:
						output_string = StringIO()
						with open(filename, 'rb') as in_file:
							parser = pdfminer.pdfparser.PDFParser(in_file)
							doc = pdfminer.pdfdocument.PDFDocument(parser)
							rsrcmgr = pdfminer.pdfinterp.PDFResourceManager()
							device = pdfminer.converter.TextConverter(rsrcmgr, output_string, laparams=pdfminer.layout.LAParams())
							interpreter = pdfminer.pdfinterp.PDFPageInterpreter(rsrcmgr, device)
							for page in pdfminer.pdfpage.PDFPage.create_pages(doc):
								interpreter.process_page(page)
						t = output_string.getvalue()
						text.append(t)
						handled = True
					
					# rtf
					ext_rtf = ['rtf']
					if ext in ext_rtf:
						with open(filename, 'r', errors='replace') as file:
							t = file.read()
							try:
								t = self.striprtf(t)
								text.append(t)
								handled = True
							except:
								hadled = False

					# text
					ext_txt = ['txt']
					if ext in ext_txt:
						with open(filename, 'r', errors='replace') as file:
							t = file.read()
							text.append(t)
							handled = True
			
			if handled:
				# combine the potential multiple documents
				text = '\n'.join(text)

				# clean text
				for key, val in replace_dict.items():
					text = text.replace(key, val)

				# Save to file
				self.to_markdown(story, text, options)

			else:
				print(f"Not handled text of {story}")
		else:
			print(f"Story {story} has text already available")

	def get_stories(self, *args, **options):
		"""
		Download stories from TOB and extract the text, and word count
		"""
		baseUrl = "https://overflowingbra.com/download.php?StoryID="

		# handle arguments
		if options['story_id']:
			stories = [Story.objects.get(id=options['story_id'])]
			options['forced'] = True
		else:
			stories = Story.objects.all()
		if options['forced']:
			options['forced_download'] = options['forced_textify'] = options['forced_wordcount'] = True

		# iterate over stories
		raw_loc = 'zone/cache/zone/stories_raw/'
		Path(raw_loc).mkdir(parents=True, exist_ok=True)
		for s in stories:
			# file of interest
			folderName=os.path.join(raw_loc, str(s.id))
			url = baseUrl + str(s.id)

			# Download story as necessary
			if not os.path.exists(folderName) or (os.path.exists(folderName) and options['forced_download']):
				print(f"Downloading {s}")
				try:
					tempname,_ = request.urlretrieve(url, "zone/cache/zone/temp.zip")
				except:
					print(f"Failed to download {s}")
					continue
				try:
					shutil.unpack_archive(tempname, folderName)
				except:
					print(f"Failed to extract {s}")
					continue

				# clear up tempfile after use
				os.remove(tempname)
			else:
				print(f"Story {s} already exists on disk")

			# Textify story as necessary (convert into markdown)
			# if s.text == "" or (not s.text == "" and options['forced_textify']):
			if True:
				print(f"Textifying {s}")
				handled = False

				# extentions that can and will be converted. Order first as highest priority. Try to order in ease of conversion to markdown, and that has relevant styling (headings, e.t.c.)
				exts = ['html', 'htm', 'doc', 'docx', 'odt', 'pdf', 'rtf', 'txt']

				# loop through file extentions in decreasing priority of conversion
				for ext in exts:
					# Find all files of this extention for this story
					filenames = []
					for filename in glob.iglob(folderName + '/**/*.' + ext, recursive=True):
						filenames.append(filename)
					if not filenames or handled:
						continue

					# text could come from multiple files, if multiple files have the same extention
					text = []					
					for filename in filenames:

						# html
						ext_html = ['html', 'htm']
						if ext in ext_html:
							t, handled = self.html2md(filename)
							text.append(t)


						# pandoc
						exts_pandoc = ['doc', 'docx', 'odt']
						if ext in exts_pandoc:
							extra_args=['--atx-headers']
							try:
								t = pypandoc.convert_file(filename, 'md', 
									extra_args=extra_args)
								text.append(t)
								handled = True
							except:
								pass

						# pdf
						ext_pdf = ['pdf']
						if ext in ext_pdf:
							output_string = StringIO()
							with open(filename, 'rb') as in_file:
								parser = pdfminer.pdfparser.PDFParser(in_file)
								doc = pdfminer.pdfdocument.PDFDocument(parser)
								rsrcmgr = pdfminer.pdfinterp.PDFResourceManager()
								device = pdfminer.converter.TextConverter(rsrcmgr, output_string, laparams=pdfminer.layout.LAParams())
								interpreter = pdfminer.pdfinterp.PDFPageInterpreter(rsrcmgr, device)
								for page in pdfminer.pdfpage.PDFPage.create_pages(doc):
									interpreter.process_page(page)
							t = output_string.getvalue()
							text.append(t)
							handled = True
						
						# rtf
						ext_rtf = ['rtf']
						if ext in ext_rtf:
							with open(filename, 'r', errors='replace') as file:
								t = file.read()
								try:
									t = self.striprtf(t)
									text.append(t)
									handled = True
								except:
									hadled = False

						# text
						ext_txt = ['txt']
						if ext in ext_txt:
							with open(filename, 'r', errors='replace') as file:
								t = file.read()
								text.append(t)
								handled = True
				
				if handled:
					# combine the potential multiple documents
					text = '\n'.join(text)

					# clean text
					for key, val in replace_dict.items():
						text = text.replace(key, val)

					# Save to file
					self.to_markdown(s, text, options)

					# Calculate word count
					if s.words == 0 or (not s.words == 0 and options['forced_wordcount']):	
						self.save_wordcount(text, s)

				else:
					print(f"Not handled text of {s.id}")
			else:
				print(f"Story {s.id} has text already available")

	def get_wordcount(self, story: Story):
		"""
		Calculate word count of story. Save to story model
		"""
		text = self.get_story_text(story)

		story.words = len(text.split())
		story.save()
		print(f"{story} has {story.words} words")

	def get_story_text(self, story: Story):
		story_dir = os.path.join('zone/static/zone/stories/', str(story.id))
		md_name = os.path.join(story_dir,str(story.id)+".md")
		text = ""
		if os.path.exists(md_name):
			with open(md_name, 'r') as f:
				text = f.read()
		return text

	def to_markdown(self, story, text, options):
		story_dir = os.path.join('zone/static/zone/stories/', str(story.id))
		Path(story_dir).mkdir(parents=True, exist_ok=True)
		md_name = os.path.join(story_dir,str(story.id)+".md")
		if not os.path.exists(md_name) or (os.path.exists(md_name) and options['forced']):
			print(f"Converting {story} to markdown")

			with open(md_name, 'w') as f:
				f.write(text)

	def html2md(self, filename):
		"""
		Take a htm(l) filename and convert it to markdown text
		"""
		with codecs.open(filename, 'r', encoding='utf-8', errors='replace') as file: 
			soup = BeautifulSoup(file, 'html5lib')
		try:
			contents = '\n'.join([str(e) for e in soup.body.contents])
		except:
			contents = '\n'.join([str(e) for e in soup.contents])
		text = markdownify(contents, heading_style="ATX")
		handled = True
		return (text, handled)

	def striprtf(self, text):
		"""
		Extract text in RTF Files. Refactored to use with Python 3.x
		Source:
			http://stackoverflow.com/a/188877
		Code created by Markus Jarderot: http://mizardx.blogspot.com
		"""
		pattern = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.I)
		# control words which specify a "destionation".
		destinations = frozenset((
			'aftncn','aftnsep','aftnsepc','annotation','atnauthor','atndate','atnicn','atnid',
			'atnparent','atnref','atntime','atrfend','atrfstart','author','background',
			'bkmkend','bkmkstart','blipuid','buptim','category','colorschememapping',
			'colortbl','comment','company','creatim','datafield','datastore','defchp','defpap',
			'do','doccomm','docvar','dptxbxtext','ebcend','ebcstart','factoidname','falt',
			'fchars','ffdeftext','ffentrymcr','ffexitmcr','ffformat','ffhelptext','ffl',
			'ffname','ffstattext','field','file','filetbl','fldinst','fldrslt','fldtype',
			'fname','fontemb','fontfile','fonttbl','footer','footerf','footerl','footerr',
			'footnote','formfield','ftncn','ftnsep','ftnsepc','g','generator','gridtbl',
			'header','headerf','headerl','headerr','hl','hlfr','hlinkbase','hlloc','hlsrc',
			'hsv','htmltag','info','keycode','keywords','latentstyles','lchars','levelnumbers',
			'leveltext','lfolevel','linkval','list','listlevel','listname','listoverride',
			'listoverridetable','listpicture','liststylename','listtable','listtext',
			'lsdlockedexcept','macc','maccPr','mailmerge','maln','malnScr','manager','margPr',
			'mbar','mbarPr','mbaseJc','mbegChr','mborderBox','mborderBoxPr','mbox','mboxPr',
			'mchr','mcount','mctrlPr','md','mdeg','mdegHide','mden','mdiff','mdPr','me',
			'mendChr','meqArr','meqArrPr','mf','mfName','mfPr','mfunc','mfuncPr','mgroupChr',
			'mgroupChrPr','mgrow','mhideBot','mhideLeft','mhideRight','mhideTop','mhtmltag',
			'mlim','mlimloc','mlimlow','mlimlowPr','mlimupp','mlimuppPr','mm','mmaddfieldname',
			'mmath','mmathPict','mmathPr','mmaxdist','mmc','mmcJc','mmconnectstr',
			'mmconnectstrdata','mmcPr','mmcs','mmdatasource','mmheadersource','mmmailsubject',
			'mmodso','mmodsofilter','mmodsofldmpdata','mmodsomappedname','mmodsoname',
			'mmodsorecipdata','mmodsosort','mmodsosrc','mmodsotable','mmodsoudl',
			'mmodsoudldata','mmodsouniquetag','mmPr','mmquery','mmr','mnary','mnaryPr',
			'mnoBreak','mnum','mobjDist','moMath','moMathPara','moMathParaPr','mopEmu',
			'mphant','mphantPr','mplcHide','mpos','mr','mrad','mradPr','mrPr','msepChr',
			'mshow','mshp','msPre','msPrePr','msSub','msSubPr','msSubSup','msSubSupPr','msSup',
			'msSupPr','mstrikeBLTR','mstrikeH','mstrikeTLBR','mstrikeV','msub','msubHide',
			'msup','msupHide','mtransp','mtype','mvertJc','mvfmf','mvfml','mvtof','mvtol',
			'mzeroAsc','mzeroDesc','mzeroWid','nesttableprops','nextfile','nonesttables',
			'objalias','objclass','objdata','object','objname','objsect','objtime','oldcprops',
			'oldpprops','oldsprops','oldtprops','oleclsid','operator','panose','password',
			'passwordhash','pgp','pgptbl','picprop','pict','pn','pnseclvl','pntext','pntxta',
			'pntxtb','printim','private','propname','protend','protstart','protusertbl','pxe',
			'result','revtbl','revtim','rsidtbl','rxe','shp','shpgrp','shpinst',
			'shppict','shprslt','shptxt','sn','sp','staticval','stylesheet','subject','sv',
			'svb','tc','template','themedata','title','txe','ud','upr','userprops',
			'wgrffmtfilter','windowcaption','writereservation','writereservhash','xe','xform',
			'xmlattrname','xmlattrvalue','xmlclose','xmlname','xmlnstbl',
			'xmlopen',
		))
		# Translation of some special characters.
		specialchars = {
			'par': '\n',
			'sect': '\n\n',
			'page': '\n\n',
			'line': '\n',
			'tab': '\t',
			'emdash': '\u2014',
			'endash': '\u2013',
			'emspace': '\u2003',
			'enspace': '\u2002',
			'qmspace': '\u2005',
			'bullet': '\u2022',
			'lquote': '\u2018',
			'rquote': '\u2019',
			'ldblquote': '\201C',
			'rdblquote': '\u201D',
		}
		stack = []
		ignorable = False       # Whether this group (and all inside it) are "ignorable".
		ucskip = 1              # Number of ASCII characters to skip after a unicode character.
		curskip = 0             # Number of ASCII characters left to skip
		out = []                # Output buffer.
		for match in pattern.finditer(text):
		# for match in pattern.finditer(text.decode()):
			word,arg,hex,char,brace,tchar = match.groups()
			if brace:
				curskip = 0
				if brace == '{':
					# Push state
					stack.append((ucskip,ignorable))
				elif brace == '}':
					# Pop state
					ucskip,ignorable = stack.pop()
			elif char: # \x (not a letter)
				curskip = 0
				if char == '~':
					if not ignorable:
						out.append('\xA0')
				elif char in '{}\\':
					if not ignorable:
						out.append(char)
				elif char == '*':
					ignorable = True
			elif word: # \foo
				curskip = 0
				if word in destinations:
					ignorable = True
				elif ignorable:
					pass
				elif word in specialchars:
					out.append(specialchars[word])
				elif word == 'uc':
					ucskip = int(arg)
				elif word == 'u':
					c = int(arg)
					if c < 0: c += 0x10000
					if c > 127: out.append(chr(c)) #NOQA
					else: out.append(chr(c))
					curskip = ucskip
			elif hex: # \'xx
				if curskip > 0:
					curskip -= 1
				elif not ignorable:
					c = int(hex,16)
					if c > 127: out.append(chr(c)) #NOQA
					else: out.append(chr(c))
			elif tchar:
				if curskip > 0:
					curskip -= 1
				elif not ignorable:
					out.append(tchar)
		return ''.join(out)

