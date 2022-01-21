from urllib import request, error
import re
import os
import datetime
import shutil
import glob
import codecs

from django.core.management import BaseCommand
from bs4 import BeautifulSoup

from zone.models import Story


def striprtf(text):
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

class StoryManager:
	"""
	Class to handle retrieving and textifying of stories
	"""
	pathname = "generated/df.json"
	df = None
	textDir = "stories_text/"

	# def load(self):
	# 	"""
	# 	load the information from file
	# 	"""
	# 	if os.path.exists(self.pathname):
	# 		self.df = pd.read_json(self.pathname, orient='index')

	# def save(self, prettify=True):
	# 	"""
	# 	save the information to file
	# 	"""
	# 	if prettify:
	# 		self.df.to_json(self.pathname, orient='index', indent=2)
	# 	else:
	# 		self.df.to_json(self.pathname)
	# 	self.df.to_csv(self.pathname[:-4]+'csv')

	def get_info(self, single=True):
		"""
		Visit the site to obtain story data

		set single=True for testing a single story
		"""
		urlYearBase = "https://overflowingbra.com/ding.htm?dates="

		htmls = []
		stories = []
		for year in range(2000,2022):
			url = urlYearBase + str(year)
			try:
				obj = request.urlopen(url)
			except error.HTTPError as e:
				print('Error code: ', e.code)
			except error.URLError as e:
				print('Reason: ', e.reason)
			htmls.append(obj.read())
			if single:
				break

		for html_doc in htmls:
			soup = BeautifulSoup(html_doc, 'html.parser')

			for i, story in enumerate(soup.find_all("div", class_="storybox")):
				author = story.find("div", class_="author").a.contents[0]
				title = story.find("div", class_="storytitle").a.contents[0]
				
				try:
					date = story.find("div", class_="submitdate").contents[0]
					date = datetime.date.strptime(date, '%dth, %b %y')
				except:
					date = datetime.date(1970, 1, 1)
				
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

				story_dict = {
					"author": author,
					"authorID": authorId,
					"title": title,
					"storyID": storyId,
					"date": date,
					"summary": summary,
					"tags": tags,
					"downloads": downloads
				}
				stories.append(story_dict)

				if single:
				# if i > 50:
					break

		# df = pd.DataFrame(stories)
		# df.set_index("storyID", inplace=True)
		# self.df = df

	def download(self, storyID, forced=False):
		"""
		Download a story
		"""

		baseUrl = "https://overflowingbra.com/download.php?StoryID="
		url = baseUrl + str(storyID)

		# Download from site
		folderName = "stories_raw"+"/"+str(storyID)
		download = True
		if os.path.exists(folderName):
			print(f"Story {storyID} already exists on disk")
			download = forced

		if download:
			print(f"Downloading {storyID}")
			try:
				tempname,_ = request.urlretrieve(url, "temp.zip")
			except:
				return (False, False)
			shutil.unpack_archive(tempname, folderName)

			# clear up tempfile after use
			os.remove(tempname)

		# Extract the text
		if storyID == '159':
			print("stop")
		textify=True
		textName = self.textDir+str(storyID)+".txt"
		if os.path.exists(textName):
			print(f"Story {storyID} has text already available")
			textify=forced
	
		if textify:
			print(f"Textifying {storyID}")
			handled = False
			# text
			for filename in glob.iglob(folderName + '/**/*.txt', recursive=True):
				with open(filename, 'r') as file:
					text = file.read()
					handled = True

			# rtf
			for filename in glob.iglob(folderName + '/**/*.rtf', recursive=True):
				with open(filename, 'r') as file:
					text = file.read()
					text= striprtf(text)
					handled = True

			# htm
			for filename in glob.iglob(folderName + '/**/*.htm', recursive=True):
				with codecs.open(filename, 'r', encoding='utf-8', errors='replace') as file: 
					soup = BeautifulSoup(file, 'html.parser')
					# remove nbsp character
					text = soup.get_text().replace('\xa0', ' ')
					handled = True

			# html
			for filename in glob.iglob(folderName + '/**/*.html', recursive=True):
				with codecs.open(filename, 'r', encoding='utf-8', errors='replace') as file: 
					soup = BeautifulSoup(file, 'html.parser')
					# remove nbsp character
					try:
						soup.prettify(formatter=lambda s: s.replace(u'\xa0', ' '))
						# remove nbsp character
						text = soup.get_text().replace('\xa0', ' ')
						handled = True
					except:
						handled = False

			if handled:
				with open(textName, 'w', encoding='utf8') as file:
					file.write(text)
			else:
				print(f"Not handled text of {storyID}")

		return (download, textify)

	def download_all(self, forced=False):
		"""
		Download all stories that are known.
		Run get_info to populate what stories exist

		force: whether to re-download if already found on disk
		"""
		downloadCounter = 0
		for index, row in self.df.iterrows():
			download, textify = self.download(index, forced)

			# create some sort of naive rate-limit
			if download:
				downloadCounter = downloadCounter + 1
				if downloadCounter % 50 == 0:
					time.sleep(4000)

	# def to_html(self, storyID):
	#     """
	#     takes a text and attempts to prettify it and create a consistent format
	#     """
	#     outfolder = "stories/"
	#     textName = "stories_text/"+str(storyID)+".txt"
	#     if not os.path.exists(textName):
	#         raise Exception("Story text does not exist") 

	#     with open(textName, 'r') as file:
	#         text = file.read()


	def tidy_text(self, storyID):
		"""
		takes a text and attempts to prettify it and create a consistent format
		"""
		outfolder = "stories/"
		textName = "stories_text/"+str(storyID)+".txt"
		if not os.path.exists(textName):
			raise Exception("Story text does not exist") 

		with open(textName, 'r') as file:
			text = file.read()

		# convert newlines to html newlines
		text = text.replace("\n", "<br><br>")

		options = {
			'page-size': 'Letter',
			'margin-top': '0.75in',
			'margin-right': '0.75in',
			'margin-bottom': '0.75in',
			'margin-left': '0.75in',
			'encoding': "UTF-8",
			'no-outline': None
		}

		pdfkit.from_string(text, outfolder + str(storyID)+".pdf", options=options)

	def tidy_text_all(self, forced=False):
		"""
		tidies all the texts.
		Will skip if already existing with forced=False
		"""
		# reduce the rows for failed stories
		df_red = self.df
		for index, row in self.df.iterrows():
			# ignore and remove from df those with failed texts
			if not os.path.exists("stories_text/"+str(index)+".txt"):
				df_red = df_red.drop(index=index)
				continue
			execute = True
			if os.path.exists("stories/"+str(index)+".pdf") and not forced:
				execute = False
			if execute:
				print(f"Tidying {index}")
				self.tidy_text(index)
		df = df_red

	def get_text_info(self, storyID=None):
		"""
		Update info dataframe with text-related data.

		Optional storyID, else for all known stories
		"""
		
		words = []

		# if storyID:
		for index, row in self.df.iterrows():
			try:
				words.append(self.get_word_count(index))
			except:
				words.append(0)
		self.df["words"] = words

	def get_word_count(self, storyID):
		"""
		Word count of a given story, by ID
		"""

		textName = "stories_text/"+str(storyID)+".txt"
		if not os.path.exists(textName):
			raise Exception("Story text does not exist") 
		
		with open(textName, 'r') as file:
			text = file.read()

		return len(text.split())

class Command(BaseCommand):
	help = 'Download stories from TOB and extract the text'

	def add_arguments(self, parser):
		parser.add_argument('--forced', help="Whether to overwrite already stored data")
		# parser.add_argument('file_limit', help="Limit number of downloaded files to this. Useful for debugging")
	
	def handle(self, *args, **options):
		baseUrl = "https://overflowingbra.com/download.php?StoryID="
		folderName='temp'

		for s in Story.objects.all():
			print(f"Downloading {s}")
			url = baseUrl + str(s.id)

			try:
				tempname,_ = request.urlretrieve(url, "temp.zip")
			except:
				return (False, False)
			shutil.unpack_archive(tempname, folderName)

			# clear up tempfile after use
			os.remove(tempname)


			print(f"Textifying {s.id}")
			handled = False
			# text
			for filename in glob.iglob(folderName + '/**/*.txt', recursive=True):
				with open(filename, 'r') as file:
					text = file.read()
					handled = True

			# rtf
			for filename in glob.iglob(folderName + '/**/*.rtf', recursive=True):
				with open(filename, 'r') as file:
					text = file.read()
					text= striprtf(text)
					handled = True

			# htm
			for filename in glob.iglob(folderName + '/**/*.htm', recursive=True):
				with codecs.open(filename, 'r', encoding='utf-8', errors='replace') as file: 
					soup = BeautifulSoup(file, 'html.parser')
					# remove nbsp character
					text = soup.get_text().replace('\xa0', ' ')
					handled = True

			# html
			for filename in glob.iglob(folderName + '/**/*.html', recursive=True):
				with codecs.open(filename, 'r', encoding='utf-8', errors='replace') as file: 
					soup = BeautifulSoup(file, 'html.parser')
					# remove nbsp character
					try:
						soup.prettify(formatter=lambda s: s.replace(u'\xa0', ' '))
						# remove nbsp character
						text = soup.get_text().replace('\xa0', ' ')
						handled = True
					except:
						handled = False

			if handled:
				with open(textName, 'w', encoding='utf8') as file:
					file.write(text)
			else:
				print(f"Not handled text of {s.id}")
			os.remove(folderName)
