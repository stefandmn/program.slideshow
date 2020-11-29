# -*- coding: utf-8 -*-

import os
from .abstract import ContentProvider


class TheAudioDB(ContentProvider):
	def __init__(self):
		self.URL_ARTISTSEARCH = 'http://www.theaudiodb.com/api/v1/json/%s/search.php'
		self.URL_ALBUMSEARCH = 'http://www.theaudiodb.com/api/v1/json/%s/searchalbum.php'
		self.ARTISTFILENAME = 'theaudiodbartistbio.nfo'
		self.ALBUMFILENAME = 'theaudiodbartistsalbums.nfo'
		self.CACHETIMEFILENAME = 'theaudiodbcachetime.nfo'
		self.ALBUMCACHETIMEFILENAME = 'theaudiodbalbumcachetime.nfo'

	def getAlbumList(self, params):
		albums = []
		self._setFilepaths(params)
		url, url_params = self._getUrlDetails(params, self.URL_ALBUMSEARCH)
		if url:
			json_data = self._getData(self.ALBUMFILEPATH, self.ALBUMCACHEFILEPATH, url, url_params)
			if json_data is not None and json_data:
				content = json_data.get('album')
				if content is not None:
					for album in content:
						albums.append((album.get('strAlbum', ''), album.get('strAlbumThumb', ''), album.get('intYearReleased', ''), album.get('strStyle', album.get('strGenre', ''))))
					if content[0].has_key("strMusicBrainzArtistID"):
						params["mbid"] = content[0].get("strMusicBrainzArtistID")
		return albums

	def getBiography(self, params):
		bio = ''
		self._setFilepaths(params)
		url, url_params = self._getUrlDetails(params, self.URL_ARTISTSEARCH)
		if url:
			json_data = self._getData(self.ARTISTFILEPATH, self.CACHEFILEPATH, url, url_params)
			if json_data is not None and json_data:
				content = json_data.get('artists')
				if content is not None:
					bio = content[0].get('strBiography' + params.get('lang', '').upper(), '')
					if content[0].has_key("strMusicBrainzID"):
						params["mbid"] = content[0].get("strMusicBrainzID")
		return self._CleanText(bio)

	def getImageList(self, params):
		images = []
		self._setFilepaths(params)
		url, url_params = self._getUrlDetails(params, self.URL_ARTISTSEARCH)
		if url:
			json_data = self._getData(self.ARTISTFILEPATH, self.CACHEFILEPATH, url, url_params)
			if json_data:
				content = json_data.get('artists')
				if content is not None:
					for i in range(1, 3):
						if i == 1:
							num = ''
						else:
							num = str(i)
						image = content[0].get('strArtistFanart' + num, '')
						if image:
							images.append(image)
					if content[0].has_key("strMusicBrainzID"):
						params["mbid"] = content[0].get("strMusicBrainzID")
		if not images:
			return []
		else:
			return self._delExclusions(images, params.get('exclusionsfile', ''))

	def _getUrlDetails(self, params, nameurl):
		url_params = {}
		if nameurl:
			nameurl = nameurl % params.get("clientapikey")
			url_params['s'] = params.get('artist', '')
			return nameurl, url_params
		else:
			return '', url_params

	def _setFilepaths(self, params):
		self.ARTISTFILEPATH = os.path.join(params.get('infodir', ''), self.ARTISTFILENAME)
		self.CACHEFILEPATH = os.path.join(params.get('infodir', ''), self.CACHETIMEFILENAME)
		self.ALBUMCACHEFILEPATH = os.path.join(params.get('infodir', ''), self.ALBUMCACHETIMEFILENAME)
		self.ALBUMFILEPATH = os.path.join(params.get('infodir', ''), self.ALBUMFILENAME)
