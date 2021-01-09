# -*- coding: utf-8 -*-

import os
import common
import xml.etree.ElementTree as _xmltree
from .abstract import ContentProvider
from utilities import ReadFile



class Local(ContentProvider):

	def __init__(self):
		self.BIOFILEPATH = os.path.join('override', 'artistbio.nfo')
		self.ALBUMFILEPATH = os.path.join('override', 'artistsalbums.nfo')


	def getImageList(self, params):
		return None


	def getAlbumList(self, params):
		albums = []
		filepath = os.path.join(params.get('localartistdir', ''), self.ALBUMFILEPATH)
		local_path = os.path.join(params.get('localartistdir', ''), params.get('artist', '').decode('utf-8'), 'override')
		common.debug('Checking ' + filepath, "local")
		rawxml = ReadFile(filepath)
		if rawxml:
			xmldata = _xmltree.fromstring(rawxml)
		else:
			return []
		aname = None
		aimage = ''
		ayear = ''
		agenre = ''
		for element in xmldata.getiterator():
			if element.tag == "name":
				if aname is not None and aimage is not None:
					albums.append((aname, aimage, ayear, agenre))
				aname = element.text
				aname.encode('ascii', 'ignore')
				aimage = ''
				ayear = ''
				agenre = ''
			elif element.tag == "image":
				image_text = element.text
				if not image_text:
					aimage = ''
				else:
					aimage = os.path.join(local_path, 'albums', image_text)
			elif element.tag == "year":
				ayear = element.text
			elif element.tag == "genre":
				agenre = element.text
		if not albums:
			common.debug('No albums found in local xml file', "local")
			return []
		else:
			return albums


	def getBiography(self, params):
		bio = ''
		filepath = os.path.join(params.get('localartistdir', ''), self.BIOFILEPATH)
		common.debug('Checking ' + filepath)
		rawxml = ReadFile(filepath)
		if rawxml:
			xmldata = _xmltree.fromstring(rawxml)
		else:
			return None
		for element in xmldata.getiterator():
			if element.tag == "content":
				bio = element.text
		if not bio:
			return None
		else:
			return bio
