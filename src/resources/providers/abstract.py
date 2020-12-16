# -*- coding: utf-8 -*-import osimport reimport abcimport sysimport timeimport jsonimport randomimport commonfrom utilities import CheckPath, ReadFile, WriteFile, DeleteFileif hasattr(sys.modules["__main__"], "xbmc"):	xbmc = sys.modules["__main__"].xbmcelse:	import xbmcclass ContentProvider(object):	__metaclass__ = abc.ABCMeta	CACHEEXPIRE = {'low': int(12 * 7 * 24 * 60 * 60), 'high': int(24 * 7 * 24 * 60 * 60)}	@abc.abstractmethod	def getImageList(self, params):		pass	@abc.abstractmethod	def getAlbumList(self, params):		pass	@abc.abstractmethod	def getBiography(self, params):		pass	def _updateCache(self, filepath, cachefilepath):		exists = CheckPath(filepath, False)		if exists:			if time.time() - os.path.getmtime(filepath) < self._getCacheTime(cachefilepath):				common.debug('Cached info found')				return False			else:				common.debug('Outdated cached info')				return self._setCacheTime(cachefilepath)		else:			common.debug('No cachetime file found, creating it')			return self._setCacheTime(cachefilepath)	def _setCacheTime(self, cachefilepath):		cachetime = random.randint(self.CACHEEXPIRE['low'], self.CACHEEXPIRE['high'])		success = WriteFile(str(cachetime), cachefilepath)		return success	def _getCacheTime(self, cachefilepath):		rawdata = None		common.debug('Getting the cache timeout information')		exists = CheckPath(cachefilepath, False)		if exists:			success = True		else:			success = self._setCacheTime(cachefilepath)		if success:			rawdata = ReadFile(cachefilepath)		if rawdata is not None and rawdata:			return int(rawdata)		else:			return 0	def _getData(self, filepath, cachefilepath, url, url_params):		json_data = None		if self._updateCache(filepath, cachefilepath):			json_data = common.urlcall(url, payload=url_params, output='json')			if json_data is not None:				WriteFile(json_data.encode('utf-8'), filepath)		exists = CheckPath(filepath, False)		if exists:			rawdata = ReadFile(filepath)			try:				json_data = json.loads(rawdata)			except ValueError:				DeleteFile(filepath)				common.debug('Deleted old cache file. New file will be download on next run')				json_data = None		return json_data	def _delExclusions(self, image_list, exclusionfilepath):		images = []		rawdata = ReadFile(exclusionfilepath)		if not rawdata:			return image_list		exclusionlist = rawdata.split()		for image in image_list:			for exclusion in exclusionlist:				if not exclusion.startswith(xbmc.getCacheThumbName(image)):					images.append(image)		return images	def _CleanText(self, text):		text = re.sub('<a [^>]*>|</a>|<span[^>]*>|</span>', '', text)		text = re.sub('&quot;', '"', text)		text = re.sub('&amp;', '&', text)		text = re.sub('&gt;', '>', text)		text = re.sub('&lt;', '<', text)		text = re.sub('User-contributed text is available under the Creative Commons By-SA License and may also be available under the GNU FDL.', '', text)		return text.strip()