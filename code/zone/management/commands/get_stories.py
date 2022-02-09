from urllib import request, error
import re
import os
import datetime
import shutil
import glob
import codecs
from pathlib import Path
from io import StringIO

from django.core.management import BaseCommand
from django.templatetags.static import static

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
from zone.models import Story


# Various strings (key) to replace with (value)
replace_dict = {
	'\00': ' ', # Null Character
	'\xa0': ' ', # remove nbsp character

}

class Command(BaseCommand):
	help = 'Download stories from TOB and extract the text, and word count'

	def add_arguments(self, parser):
		parser.add_argument('--forced', action="store_true", help="Overwrite already stored data. Equivalent to all the other optional arguments together")
		parser.add_argument('--forced_download', action="store_true", help="Re-download stories")
		parser.add_argument('--forced_textify', action="store_true", help="Overwrite text data")
		parser.add_argument('--forced_wordcount', action="store_true", help="Overwrite word count")
		parser.add_argument('--story_id', help="Download a particular story (if already known about in database)")
	
	def handle(self, *args, **options):
		baseUrl = "https://overflowingbra.com/download.php?StoryID="

		if options['story_id']:
			stories = [Story.objects.get(id=options['story_id'])]
			options['forced'] = True
		else:
			stories = Story.objects.all()

		if options['forced']:
			options['forced_download'] = options['forced_textify'] = options['forced_wordcount'] = True

		raw_loc = 'zone/cache/zone/stories_raw/'
		Path(raw_loc).mkdir(parents=True, exist_ok=True)
		for s in stories:
			folderName=os.path.join(raw_loc, str(s.id))

			url = baseUrl + str(s.id)

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


			if s.text == "" or (not s.text == "" and options['forced_textify']):
				print(f"Textifying {s}")
				handled = False

				exts = ['html', 'htm', 'doc', 'docx', 'odt', 'pdf', 'rtf', 'txt']

				# loop through file extentions in decreasing priority of conversion
				for ext in exts:
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
								break
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

					# # clean text
					for key, val in replace_dict.items():
						text = text.replace(key, val)

					s.text = text
					s.save()
				else:
					print(f"Not handled text of {s.id}")
			else:
				print(f"Story {s.id} has text already available")

			if s.words == 0 or (not s.words == 0 and options['forced_wordcount']):
				s.words = len(s.text.split())
				s.save()

	def html2md(self, filename):
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

