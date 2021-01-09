# -*- coding: utf-8 -*-

import re
import common
from .abstract import ContentProvider


class DuckGo(ContentProvider):

	def __init__(self):
		self.DDG_SEARCH_URL = 'https://duckduckgo.com/'


	def getImageList(self, params):
		common.trace("Starting to search images using parameters: %s" %str(params), "duckgo")
		images = []
		if params.get('mbid', '') == '':
			common.warn("No artist identified over MusicBrainz, search stopped")
			return images
		if "fullname" in params and not common.isempty(params['fullname']):
			keywords = params['fullname'] + " AND (singer OR band)"
		elif "alias" in params and not common.isempty(params['alias']):
			keywords = params['alias'] + " AND (singer OR band)"
		elif "artist" in params and not common.isempty(params['artist']):
			keywords = params['artist'] + " AND (singer OR band)"
		else:
			keywords = None
		if keywords is not None and "location" in params and not common.isempty(params['location']):
			keywords = keywords + " AND " + params['location']
		elif keywords is not None and "lang" in params and not common.isempty(params['lang']):
			keywords = keywords + " AND " + params['lang']
		if keywords is not None:
			payload = {'q': keywords}
			common.trace("Hitting DuckDuckGo for token", "duckgo")
			data = common.urlcall(self.DDG_SEARCH_URL, "POST", payload=payload)
			searchObj = re.search(r'vqd=([\d-]+)\&', data, re.M | re.I)
			if not searchObj:
				common.error("Token parsing failed!", "duckgo")
				return images
			else:
				common.debug("Obtained token: %s" % searchObj.group(1), "duckgo")
			headers = {
				'authority': 'duckduckgo.com',
				'accept': 'application/json, text/javascript, */*; q=0.01',
				'sec-fetch-dest': 'empty',
				'x-requested-with': 'XMLHttpRequest',
				'user-agent': common.agent(),
				'sec-fetch-site': 'same-origin',
				'sec-fetch-mode': 'cors',
				'referer': 'https://duckduckgo.com/'
			}
			payload = {
				"q": keywords,
				"vqd": searchObj.group(1),
				"v7exp": "a",
				"o": "json",
				"l": "wt-wt",
				"f": ",,,",
				"p": '1'
			}
			data = None
			while True:
				try:
					data = common.urlcall(self.DDG_SEARCH_URL + "i.js", headers=headers, payload=payload, output='json')
					break
				except ValueError as e:
					common.trace("Calling url failure; sleep and retry", "duckgo")
					common.sleep(500)
					continue
			index = 0
			max = common.any2int(params['limit'], 0)
			for obj in data["results"]:
				contextual = str(obj["title"].encode('utf-8')).lower().find(params['artist'].lower() + " ") >= 0
				dimension = int(obj["width"]) >= 876 if common.any2bool(params.get('getall', 'false')) else int(obj["width"]) >= 1920
				if contextual and dimension:
					index += 1
					images.append(obj["image"])
				if max > 0 and index >= max:
					break
		if not images:
			return []
		else:
			return self._delExclusions(images, params.get('exclusionsfile'))


	def getAlbumList(self, params):
		return None


	def getBiography(self, params):
		return None
