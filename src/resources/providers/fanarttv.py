# -*- coding: utf-8 -*-

import os
import urllib
from abstract import ContentProvider


class FanartTV(ContentProvider):
	def __init__(self):
		self.URL_MUSICSEARCH = 'http://webservice.fanart.tv/v3/music/'
		self.FILENAME = 'fanarttvartistimages.nfo'
		self.CACHETIMEFILENAME = 'fanarttvcachetime.nfo'

	def getImageList(self, params):
		images = []
		url_params = {}
		filepath = os.path.join(params.get('infodir', ''), self.FILENAME)
		cachefilepath = os.path.join(params.get('infodir', ''), self.CACHETIMEFILENAME)
		if params.get('mbid', '') == '':
			params['mbid'] = self.getMusicBrainzID(params['artist'])
		url = self.URL_MUSICSEARCH + params.get('mbid', '')
		url_params['api_key'] = params.get("clientapikey")
		json_data = self._getData(filepath, cachefilepath, url, url_params)
		if json_data is not None and json_data:
			image_list = json_data.get('artistbackground', [])
			if params.get('getall', 'false') == 'true':
				image_list.extend(json_data.get('artistthumb', []))
			for image in image_list:
				url = image.get('url', '')
				if url:
					images.append(url)
		if not images:
			return []
		else:
			return self._delExclusions(images, params.get('exclusionsfile'))

	def getAlbumList(self, params):
		return None

	def getBiography(self, params):
		return None

	def getMusicBrainzID(self, artist):
		if isinstance(artist, list):
			tag = urllib.quote(artist[0])
		else:
			tag = urllib.quote(artist)
		success, json_data = self.JSONURL.Get("http://musicbrainz.org/ws/2/artist/?query=artist:%s&fmt=json" %tag)
		if success and json_data["artists"]:
			return json_data["artists"][0]["id"]
		else:
			return ''