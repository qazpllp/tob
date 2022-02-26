from urllib import request, error
import re
import os
import datetime
import shutil
import glob
import codecs
from pathlib import Path
from io import StringIO
from typing import List

from django.core.management import BaseCommand
from django.templatetags.static import static
from django.core.files import File

from bs4 import BeautifulSoup
from markdownify import markdownify
from docx import Document
import pypandoc
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import pdfminer
import markdown
import pdfkit

from django.conf import settings
from zone.models import Author, Story, Tag

# Various strings (key) to replace with (value)
replace_dict = {
	'\00': ' ', # Null Character
	'\xa0': ' ', # remove nbsp character

}

class Command(BaseCommand):
	help = 'Download stories from TOB and extract the text, and word count'

	cache_loc = os.path.join(settings.CACHE_ROOT,'zone/')
	raw_cache_loc = os.path.join(cache_loc,'story_raw/')
	baseUrl = "https://overflowingbra.com/download.php?StoryID="
	# static_dir = os.path.join(settings.CACHE_ROOT,'zone/static/zone/stories/')

	def add_arguments(self, parser):
		parser.add_argument('--forced', action="store_true", help="Overwrite already stored data. Equivalent to all the other optional arguments together")
		parser.add_argument('--forced_download', action="store_true", help="Re-download stories")
		parser.add_argument('--forced_textify', action="store_true", help="Overwrite text data")
		parser.add_argument('--forced_wordcount', action="store_true", help="Overwrite word count")
		parser.add_argument('--forced_convert', action="store_true", help="Overwrite pdf/html, e.t.c. files for serving")
		parser.add_argument('--skip_find', action="store_true", help="Overwrite pdf/html, e.t.c. files for serving")
		parser.add_argument('--story_id', help="Download a particular story (if already known about in database)")
		parser.add_argument('--year', help='Optional comma separated list of years to search')
		parser.add_argument('--update', action="store_true", help='Only finds and consideres newly added stories to textify')

	def handle(self, *args, **options):
		baseUrl = "https://overflowingbra.com/download.php?StoryID="

		if options['story_id']:
			options['skip_find'] = options['forced'] = True
		if options['forced']:
			options['forced_download'] = options['forced_textify'] = options['forced_wordcount'] = options['forced_convert'] = True

		# find stories
		if not options['skip_find']:
			htmls = self.get_tob_pages(**options)
			new_stories = []
			for html in htmls:
				new_stories += self.add_stories_by_year(html)

		# iterate over stories
		# handle arguments
		if options['story_id']:
			stories = [Story.objects.get(id=options['story_id'])]
			options['forced'] = True
		elif options['update']:
			stories = new_stories
		else:
			stories = Story.objects.all()
		Path(self.cache_loc).mkdir(parents=True, exist_ok=True)
		for s in stories:
			self.download_to_cache(s, **options)
			self.cache_to_markdown(s, **options)
			self.get_wordcount(s, **options)
			self.convert_text(s, **options)

	def get_tob_pages(self, *args, **options) -> List[str]:
		"""
		Scrape TOB site to find pages with all the stories, by year
		Returns a list of 1 html page per year 
		"""
		urlYearBase = "https://overflowingbra.com/ding.htm?dates="
		htmls = []

		if options['year']:
			years = [int(s.strip()) for s in options["year"].split(",")]
		elif options['update']:
			years = years = [datetime.datetime.now().year]
		else:
			years = range(1998, datetime.datetime.now().year + 1)

		# Find available stories by searching by year
		for year in years:
			
			# store pages for later use
			html_path = os.path.join(self.cache_loc,'year_html/')
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
		return htmls

	def add_stories_by_year(self, html_doc: str, *args, **options) -> List[Story]:
		"""
		Takes a html doc containing potential stories and extracts story/author info
		"""
		soup = BeautifulSoup(html_doc, 'html.parser')
		new_stories = []

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
			story, created_s = Story.objects.get_or_create(
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
			# If not created, update with more recent values
			else:
				story.downloads = downloads
				story.save()

			if created_a:
				print(f"Creating author {author}")
			if created_s:
				print(f"Creating Story {story}")
				new_stories.append(story)
		return new_stories

	def download_to_cache(self, s: Story, *args, **options):
		"""
		Download original files from original site, when appropriate.
		Returns whether successed to create the files.
		"""			
		# file of interest
		folderName=os.path.join(self.raw_cache_loc, str(s.id))
		url = self.baseUrl + str(s.id)

		# Download story as necessary
		if options['forced_download'] or (not s.text and not os.path.exists(folderName)):
			print(f"Downloading {s}")
			temploc = os.path.join(self.cache_loc, "temp.zip")
			Path(os.path.dirname(temploc)).mkdir(parents=True, exist_ok=True)
			try:
				tempname,_ = request.urlretrieve(url, temploc)
			except:
				print(f"Failed to download {s}")
				return False
			try:
				shutil.unpack_archive(tempname, folderName)
			except:
				print(f"Failed to extract {s}")
				return False

			# clear up zip file after use
			os.remove(tempname)
		else:
			print(f"Story {s} already exists on disk")
		return True

	def cache_to_markdown(self, s: Story, *args, **options):
		"""
		Textify story as necessary (convert into markdown)
		"""
		if s.text and not options['forced_textify']:
			print(f"Story {s.id} has text already available")
			return

		print(f"Textifying {s}")
		handled = False
		folderName=os.path.join(self.raw_cache_loc, str(s.id))

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
						for page in PDFPage.create_pages(doc):
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
							t = self.txt2markdown(t)
							text.append(t)
							handled = True
						except:
							hadled = False

				# text
				ext_txt = ['txt']
				if ext in ext_txt:
					with open(filename, 'r', errors='replace') as file:
						t = file.read()
						t = self.txt2markdown(t)
						text.append(t)
						handled = True
		
		if handled:
			# combine the potential multiple documents
			text = '\n'.join(text)

			# clean text
			for key, val in replace_dict.items():
				text = text.replace(key, val)

			# Save to file
			if not s.text or options['forced_textify']:
				# make a markdown file
				mdpath = Path('temp.md')
				with mdpath.open(mode='w') as f:
					f.write(text)
				# save this markdown file to the model
				with mdpath.open(mode='r') as f:
					s.text = File(f, name=f'{s.id}.md')
					s.save()
				# delete the temp markdown file
				os.remove(mdpath)

		else:
			print(f"Not handled text of {s}")

	def get_wordcount(self, s: Story, *args, **options):
		if (options['forced_wordcount'] or s.words == 0) and s.text:
			with s.text.open() as f:
				text = f.read()	
			s.words = len(text.split())
			s.save()
			print(f"Story {s} has {s.words} words")

	def convert_text(self, s: Story, *args, **options):
		if not s.text:
			print(f'{s} has no text to convert')
			return

		story_dir = os.path.join(self.cache_loc, "conv_story", str(s.id))
		Path(story_dir).mkdir(parents=True, exist_ok=True)
		
		# html
		if options['forced_convert'] or not s.text_html:
			print(f"Converting {s} to html")

			# remove old file
			s.text_html.delete()

			with s.text.open('r') as f:
				text = f.read()

			html_name = os.path.join(story_dir,str(s.id)+".html")
			html = markdown.markdown(text)
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

			# attach as part of the model
			with open(html_name, 'r') as f:
				s.text_html = File(f, name=f'{s.id}.html')
				s.save()
			os.remove(html_name)

		# pdf 
		if options['forced_convert'] or not s.text_pdf:
			# remove old file
			s.text_pdf.delete()

			pdf_name = os.path.join(story_dir,str(s.id)+".pdf")
			print(f"Converting {s} to pdf")

			opts = {
				'page-size': 'Letter',
				'margin-top': '0.75in',
				'margin-right': '0.75in',
				'margin-bottom': '0.75in',
				'margin-left': '0.75in',
				'encoding': "UTF-8",
				'enable-local-file-access': None,
				'title': f"{s.title}.pdf",
			}

			# format newlines for html
			with s.text_html.open('r') as f:
				try:
					pdfkit.from_file(f, pdf_name, options=opts)
				except:
					pass
			with open(pdf_name, 'rb') as f:
				s.text_pdf = File(f, name=f'{s.id}.pdf')
				s.save()
			os.remove(pdf_name)


	def html2md(self, filename):
		"""
		Take a htm(l) filename and convert it to markdown text
		"""
		with codecs.open(filename, 'r', encoding='utf-8', errors='ignore') as file: 
			soup = BeautifulSoup(file, 'html5lib')
		# remove single newlines within <p>
		# Double newlines for ending <p> tags, to ensure newline generated
		contents = '\n\n'.join([str(e) for e in soup.stripped_strings])
		text = markdownify(contents, heading_style="ATX")
		return (text, True)

	def striprtf(self, text):
		"""
		Extract text in RTF Files. Refactored to use with Python 3.x
		Source:
			http://stackoverflow.com/a/188877
		Code created by Markus Jarderot: http://mizardx.blogspot.com
		"""
		"""
		Current issues: missing text alignment location (i.e. center text)
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

	def txt2markdown(self, text):
		"""
		Converts (plain) text to markdown.
		"""
		# Convert single newlines to double - so they are visible in MD
		text = "\n\n".join(text.split("\n"))

		# Escape MD characters
		replace = {
			"<": "&lt;",
			">": "&gt;",
		}
		for r,replacement in replace.items():
			text = text.replace(r, replacement)

		return text