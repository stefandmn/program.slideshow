# -*- coding: utf-8 -*-

import os
import re
import common
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
					if "strMusicBrainzArtistID"in content[0]:
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
					if "strMusicBrainzID" in content[0]:
						params["mbid"] = content[0].get("strMusicBrainzID")
		return self._CleanText(bio)


	def getImageList(self, params):
		common.trace("Starting to search images using parameters: %s" % str(params), "theaudiodb")
		images = []
		self._setFilepaths(params)
		url, url_params = self._getUrlDetails(params, self.URL_ARTISTSEARCH)
		if url:
			json_data = self._getData(self.ARTISTFILEPATH, self.CACHEFILEPATH, url, url_params)
			if json_data:
				content = json_data.get('artists')
				if content is not None:
					if "strMusicBrainzID" in content[0]:
						params["mbid"] = content[0].get("strMusicBrainzID")
					if "strArtistFanart" in  content[0]:
						image = content[0].get('strArtistFanart')
						if image:
							images.append(image)
					if "strArtistFanart2" in  content[0]:
						image = content[0].get('strArtistFanart2')
						if image:
							images.append(image)
					if "strArtistFanart3" in  content[0]:
						image = content[0].get('strArtistFanart3')
						if image:
							images.append(image)
					if "strArtistThumb" in  content[0]:
						image = content[0].get('strArtistWideThumb')
						if image:
							images.append(image)
					if "strArtistWideThumb" in  content[0]:
						image = content[0].get('strArtistWideThumb')
						if image:
							images.append(image)
					if "strArtistClearart" in  content[0]:
						image = content[0].get('strArtistClearart')
						if image:
							images.append(image)
					if "strArtistAlternate" in content[0] and not common.isempty(content[0].get('strArtistAlternate')):
						params['fullname'] = content[0].get('strArtistAlternate')
					if "strArtist" in content[0] and not common.isempty(content[0].get('strArtist')):
						params['alias'] = content[0].get('strArtist')
					if "strCountryCode" in content[0] and not common.isempty(content[0].get('strCountryCode')):
						params['location'] = content[0].get('strCountryCode')
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
