# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import common
import utilities
import traceback
from resources.providers import ContentProvider

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc

if hasattr(sys.modules["__main__"], "xbmcgui"):
	xbmcgui = sys.modules["__main__"].xbmcgui
else:
	import xbmcgui

if hasattr(sys.modules["__main__"], "xbmcvfs"):
	xbmcvfs = sys.modules["__main__"].xbmcvfs
else:
	import xbmcvfs



class MediaSlideshow(xbmc.Player):
	PROVIDERS = {}


	def __init__(self):
		common.debug('%s v%s has been started' % (common.AddonName(), common.AddonVersion()))
		try:
			if len(sys.argv) >= 2:
				params = dict(arg.split("=") for arg in sys.argv[1].split("&"))
				self._winid = params.get("window", "12006")
			else:
				self._winid = "12006"
				self.window = xbmcgui.Window(int(self._winid))
		except Exception as ex:
			common.error('Unexpected error while parsing arguments: %s' % str(ex))
		if self.addonrunning:
			common.debug('Script already running, no additional instance is needed')
		else:
			self._nice()
			self._providers()
			if bool(self.PROVIDERS):
				self.execute()
			else:
				common.error("No data provider detected!")
		common.debug('%s v%s has been terminated' % (common.AddonName(), common.AddonVersion()))


	def execute(self):
		# get settings
		self.__BIOLANGUAGE = common.getAddonSetting("biography_language")
		self.__RESTRICTCACHE = common.setting("restrict_cache")
		self.__MAXCACHESIZE = common.any2int(common.setting("max_cache_size")) * 1000000
		# define workflow resources (paths)
		self.dir_root = xbmc.translatePath(common.AddonProfile()).decode('utf-8')
		utilities.CheckPath(os.path.join(self.dir_root, ''))
		self.dir_data = xbmc.translatePath('special://profile/addon_data/%s/data' % common.AddonId()).decode('utf-8')
		utilities.CheckPath(os.path.join(self.dir_data, ''))
		self.dir_merge = xbmc.translatePath('special://profile/addon_data/%s/merge' % common.AddonId()).decode('utf-8')
		utilities.CheckPath(os.path.join(self.dir_merge, ''))
		# mark workflow process as started
		self.setSkinProperty("SlideshowAddon")
		self.setSkinProperty("SlideshowAddon.Running", "True")
		# initialize workflow variables
		self._lastcachetrim = 0
		self._latestplaying = None
		self._cleanupsignal = True
		while not xbmc.abortRequested and self.addonrunning:
			if xbmc.Player().isPlayingAudio() and self._isPlaybackChanged(True):
				self.workflow(True)
			elif self._cleanupsignal:
				self.workflow(False)
				self._cleanupsignal = False
			xbmc.sleep(3000)


	def workflow(self, trigger=False):
		common.debug("Running slideshow workflow %s trigger for data collection" %("with" if trigger else "without"))
		try:
			self._setInitProperties()
			self._setCleanedDirectory(self.dir_merge)
			if trigger:
				self._setSlideshowCollection()
				self._setTrimmedCache()
		except BaseException as be:
			common.error("Error running slideshow workflow: %s" % str(be))
			if common.istrace:
				traceback.print_exc()


	def _nice(self):
		try:
			os.nice(19)
			common.notice('Set lowest priority for the global process execution')
		except Exception as e:
			common.warn('Setting niceness failed: %s' % str(e))


	def _providers(self):
		# read and load plugins
		common.debug('Discovering content providers')
		for cls in ContentProvider.__subclasses__():
			try:
				plugin = cls()
				module = str(cls.__name__).lower()
				if (module == 'local' or common.any2bool(common.setting(module))) and not module in self.PROVIDERS:
					self.PROVIDERS[module] = plugin
					common.debug('Loading provider: %s ' %module)
			except BaseException as be:
				common.error('Unexpected error while loading [%s] provider: %s' %(str(cls),str(be)))


	def _setSlideshowCollection(self):
		common.debug("Starting slideshow collection")
		artistsArray = self.getArtistNames()
		artistsCount = len(artistsArray)
		artistsIndex = 0
		for artist in artistsArray:
			if self._isPlaybackChanged():
				common.debug("Cancel slideshow collection due to the change of player content")
				break
			if artist is None or artist == '':
				continue
			artistsIndex += 1
			common.debug("Collecting slideshow for artist [%s]" % str(artist))
			self.dir_cache = self._resdir(artist)
			common.trace('Cache directory for artist [%s]: %s' % (artist, self.dir_cache))
			self._setSkinSlideshow(self.dir_merge, self.dir_cache)
			if artistsIndex == 1:
				self._setSkinArtistBiografy(artist)
				self._setSkinArtistAlbumInfo(artist)
			self._setSkinArtistImages(artist)
			self._cache2merge()
			self._setSkinSlideshow(self.dir_cache, self.dir_merge)
			common.sleep()
		common.debug('Ended slideshow collection')


	def _setSkinArtistBiografy(self, artist):
		common.debug("Collecting biography for artist: %s" %artist)
		biography = ''
		params = {}
		params['infodir'] = self.dir_cache
		params['lang'] = self.__BIOLANGUAGE
		params['artist'] = artist
		for key in self.PROVIDERS.keys():
			if self._isPlaybackChanged():
				common.debug("Cancel collecting biography due to the change of player content")
				break
			common.trace('Collecting biography from provider: [%s]' % key)
			params['getall'] = common.getAddonSetting(key + "_all")
			params['clientapikey'] = common.getAddonSetting(key + "_apikey")
			content = self.PROVIDERS[key].getBiography(params)
			if content is not None and content and len(content) > len(biography):
				common.trace('Stored new biography from provider [%s]' % key)
				biography = content
		self.setSkinProperty("SlideshowAddon.Biography", biography)
		common.trace("Biography setup is done")


	def _setSkinArtistAlbumInfo(self, artist):
		common.debug("Collecting album information for artist: %s" % artist)
		albums = []
		params = {}
		params['infodir'] = self.dir_cache
		params['lang'] = self.__BIOLANGUAGE
		params['artist'] = artist
		for key in self.PROVIDERS.keys():
			if self._isPlaybackChanged():
				common.debug("Cancel collecting album information due to the change of player content")
				break
			common.debug('Collecting album information from provider: [%s]' % key)
			params['getall'] = common.getAddonSetting(key + "_all")
			params['clientapikey'] = common.getAddonSetting(key + "_apikey")
			content = self.PROVIDERS[key].getAlbumList(params)
			if content is not None and len(content) > len(albums):
				common.debug('Stored album information from provider [%s], found up to %d albums' %(key, min(10,len(content))))
				albums = content
		index = 0
		for item in albums:
			index += 1
			self.setSkinProperty("SlideshowAddon.%d.AlbumName" %index, item[0])
			self.setSkinProperty("SlideshowAddon.%d.AlbumThumb" %index, item[1])
			self.setSkinProperty("SlideshowAddon.%d.AlbumYear" %index, item[2])
			self.setSkinProperty("SlideshowAddon.%d.AlbumGenre" %index, item[3])
			if index >= 10:
				break
		self.setSkinProperty("SlideshowAddon.AlbumCount", str(index))
		common.trace("Album information setup is done")


	def _setSkinArtistImages(self, artist):
		common.debug("Collecting images for artist: %s" %artist)
		images = []
		params = {}
		params['lang'] = self.__BIOLANGUAGE
		params['artist'] = artist
		params['infodir'] = self.dir_cache
		params['exclusionsfile'] = os.path.join(self.dir_cache, "_exclusions.nfo")
		for key in self.PROVIDERS.keys():
			if self._isPlaybackChanged():
				common.debug("Cancel collecting images due to the change of player content")
				return
			common.debug('Identifying images by provider: [%s]' %key)
			params['getall'] = common.getAddonSetting(key + "_all")
			params['clientapikey'] = common.getAddonSetting(key + "_apikey")
			content = self.PROVIDERS[key].getImageList(params)
			if content is not None and len(content) > 0:
				images.extend(content)
		common.trace('Downloading images for artist [%s]' %artist)
		_, cachefiles = xbmcvfs.listdir(self.dir_cache)
		for url in images:
			if self._isPlaybackChanged():
				common.debug("Cancel downloading images due to the change of player content")
				break
			common.trace('Checking image URL: %s' %url)
			cachepath = utilities.ItemHashWithPath(url, self.dir_cache) + utilities.ImageType(url)
			if os.path.split(cachepath)[1] not in cachefiles and not xbmc.abortRequested and not self._isPlaybackChanged():
				common.trace('Downloading image file: %s' %cachepath)
				urldata = common.urlcall(url, output='binary')
				success = utilities.WriteFile(urldata, cachepath) if urldata else False
				if success and xbmcvfs.Stat(cachepath).st_size() < 999:
					utilities.DeleteFile(cachepath)
		common.trace("Images setup is done")


	def _setSkinSlideshow(self, dir1=None, dir2=None):
		if (dir1 is None or dir1 == '' or not os.path.isdir(dir1) or dir1 == self.dir_root) and (dir2 is None or dir2 == '' or not os.path.isdir(dir2)):
			common.debug('Set slideshow location to ROOT: %s' %dir1)
			self._setProperty("SlideshowAddon", dir1)
		elif dir1 is not None and dir1 != '' and os.path.isdir(dir1) and (dir2 is None or dir2 == '' or not os.path.isdir(dir2)):
			common.debug('Set slideshow primary location: %s' % dir1)
			self.setSkinProperty("SlideshowAddon", dir1)
		elif (dir1 is None or dir1 == '' or not os.path.isdir(dir1) or dir1 == self.dir_root) and (dir2 is not None and dir2 != '' and os.path.isdir(dir2)):
			common.debug('Set slideshow secondary location: %s' % dir2)
			self._setProperty("SlideshowAddon", self.dir_root)
			common.sleep(1000)
			self.setSkinProperty("SlideshowAddon", dir2)
		elif (dir1 is not None and dir1 != '' and os.path.isdir(dir1) and dir1 != self.dir_root) and (dir2 is not None and dir2 != '' and os.path.isdir(dir2) and dir2 != self.dir_root):
			if dir1 != self.addoninfo:
				common.debug('Set slideshow temporary location: %s' % dir1)
				self.setSkinProperty("SlideshowAddon", dir1)
				common.sleep(1000)
			if dir2 != self.addoninfo:
				common.debug('Set slideshow target location: %s' % dir2)
				self.setSkinProperty("SlideshowAddon", dir2)


	def getArtistNames(self):
		featuring = None
		artists = []
		if xbmc.Player().isPlayingAudio():
			time.sleep(1.5)
			playingFile = xbmc.Player().getPlayingFile()
			artistTag = xbmc.Player().getMusicInfoTag().getArtist().strip()
			titleTag = xbmc.Player().getMusicInfoTag().getTitle().strip()
			common.debug("Discovering artist details for: artist(s) = %s, title = %s, file = %s" %(artistTag, titleTag, playingFile))
			if self._isempty(artistTag) and playingFile is not None and playingFile != '':
				lastFileSep = playingFile.rfind(os.sep) + 1 if playingFile.count(os.sep, 0) > 0 else (playingFile.rfind(os.altsep) + 1 if playingFile.count(os.altsep, 0) > 0 else 0)
				lastExtSep = playingFile.rfind(os.extsep) if playingFile.count(os.extsep, lastFileSep) else len(playingFile) - 1
				fileparts = playingFile[lastFileSep:lastExtSep].split("-")
				if len(fileparts) == 1:
					artists = self._getSplitArtists(fileparts[0].strip())
					featuring = self._getFeaturedArtists(fileparts[0].strip())
				elif len(fileparts) == 2:
					artists = self._getSplitArtists(fileparts[0].strip())
					featuring = self._getFeaturedArtists(fileparts[1].strip())
				elif len(fileparts) > 2:
					artists = self._getSplitArtists(fileparts[0].strip())
					featuring = self._getFeaturedArtists("-".join(fileparts[1:len(fileparts)]).strip())
			elif not self._isempty(artistTag):
				artists = self._getSplitArtists(artistTag)
				artists = map(str.strip, artists)
				featuring = self._getFeaturedArtists(titleTag)
			if featuring is not None and len(featuring) > 0:
				featuring = map(str.strip, featuring)
				common.debug('Adding featuring artists in the list: %s' % str(featuring))
				artists.extend(featuring)
			common.debug('Found the following artists: %s' % str(artists))
		return artists


	def _getFeaturedArtists(self, data):
		replace_regex = re.compile(r"ft\. ", re.IGNORECASE)
		split_regex = re.compile(r"feat\. ", re.IGNORECASE)
		the_split = split_regex.split(replace_regex.sub('feat.', data))
		if len(the_split) > 1:
			return self._getSplitArtists(the_split[-1])
		else:
			return []


	def _getSplitArtists(self, response):
		response = response.replace('(', '').replace(')', '')
		response = response.replace(' ft. ', '/').replace(' feat. ', '/').replace(' Ft. ', '/').replace(' Feat. ', '/')
		response = response.replace(' ft ', '/').replace(' feat ', '/').replace(' Ft ', '/').replace(' Feat ', '/')
		response = response.replace(' and ', '/').replace(' And ', '/').replace(' & ', '/')
		response = response.replace(' , ', '/').replace(', ', '/').replace(' ,', '/').replace(',', '/')
		return response.split('/')


	def _setInitProperties(self):
		common.debug('Initializing skin properties')
		self.setSkinProperty("SlideshowAddon")
		self.setSkinProperty("SlideshowAddon.Biography")
		prevAlbumCount = common.any2int(self.getSkinProperty("SlideshowAddon.AlbumCount"), none=10)
		for idx in range(1, prevAlbumCount+1):
			self.setSkinProperty("SlideshowAddon.%d.AlbumName" %idx)
			self.setSkinProperty("SlideshowAddon.%d.AlbumThumb" %idx)
			self.setSkinProperty("SlideshowAddon.%d.AlbumYear" %idx)
			self.setSkinProperty("SlideshowAddon.%d.AlbumGenre" %idx)
		self.setSkinProperty("SlideshowAddon.AlbumCount")


	def _setCleanedDirectory(self, dir):
		if dir == self.addoninfo:
			self._setSkinSlideshow()
		common.debug('Cleaning directory: %s' % dir)
		try:
			_, oldfiles = xbmcvfs.listdir(dir)
		except BaseException as e:
			common.error('Unexpected error while getting directory list: %s' % str(e))
			oldfiles = []
		for oldfile in oldfiles:
			if not oldfile.endswith('.nfo') and dir != self.dir_merge:
				utilities.DeleteFile(os.path.join(dir, oldfile.decode('utf-8')))
			elif dir == self.dir_merge:
				utilities.DeleteFile(os.path.join(dir, oldfile.decode('utf-8')))


	def _setTrimmedCache(self):
		if self.__RESTRICTCACHE and self.__MAXCACHESIZE is not None:
			now = time.time()
			cache_trim_delay = 0  # delay time is in seconds
			if now - self._lastcachetrim > cache_trim_delay:
				common.debug('Trimming the cache down to %s bytes' % self.__MAXCACHESIZE)
				cache_root = xbmc.translatePath('special://profile/addon_data/%s/data/' % common.AddonId()).decode('utf-8')
				folders, fls = xbmcvfs.listdir(cache_root)
				folders.sort(key=lambda x: os.path.getmtime(os.path.join(cache_root, x)), reverse=True)
				cachesize = 0
				firstfolder = True
				for folder in folders:
					if self._isPlaybackChanged():
						common.debug("Cancel cache trimming due to the change of player content")
						break
					cachesize = cachesize + self._folderSize(os.path.join(cache_root, folder))
					common.debug('Looking at folder %s cache size is now %s' % (folder, cachesize))
					if cachesize > self.__MAXCACHESIZE and not firstfolder:
						self._setCleanedDirectory(os.path.join(cache_root, folder))
						common.debug('Deleted files in folder %s' % folder)
					firstfolder = False
				self._lastcachetrim = now


	def _isPlaybackChanged(self, update=False):
		if xbmc.Player().isPlayingAudio():
			try:
				nowPlayingFile = xbmc.Player().getPlayingFile()
				if str(nowPlayingFile).startswith("pipe://") or str(nowPlayingFile).startswith("pvr://"):
					nowPlayingFile = xbmc.Player().getMusicInfoTag().getArtist() + " - " + xbmc.Player().getMusicInfoTag().getTitle() + ".raw"
			except:
				nowPlayingFile = None
		else:
			nowPlayingFile = None
		changed = nowPlayingFile != self._latestplaying
		common.debug("Checking player content: %s" %(("it has updates - [" + str(self._latestplaying) + "] to [" + str(nowPlayingFile) + "]") if changed else ("no updates - [" + str(nowPlayingFile) + "]")))
		if update:
			self._latestplaying = nowPlayingFile
		return changed


	def setSkinProperty(self, name, value=None):
		if value is None:
			value = ""
		try:
			self.window.setProperty(name, value)
		except BaseException as e:
			common.error("Couldn't set [%s] property to [%s] value: %s" % (name, value, str(e)))


	def getSkinProperty(self, item):
		if item is not None and item != '':
			if not str(item).lower().strip().startswith("window"):
				item = "Window(%s).Property(%s)" % (self._winid, str(item).strip())
			else:
				item = str(item).strip()
			try:
				value = xbmc.getInfoLabel(item)
			except BaseException as e:
				common.error("Couldn't read [%s] property value: %s" % (item, str(e)))
				value = ''
			return value
		else:
			return None


	@property
	def addoninfo(self):
		return common.any2bool(self.getSkinProperty("SlideshowAddon"))


	@property
	def addonrunning(self):
		return common.any2bool(self.getSkinProperty("SlideshowAddon.Running"))


	def _cache2merge(self):
		_,cachelist = xbmcvfs.listdir(self.dir_cache)
		for file in cachelist:
			if file.lower().endswith('tbn') or file.lower().endswith('jpg') or file.lower().endswith('jpeg') or file.lower().endswith('gif') or file.lower().endswith('png'):
				img_source = os.path.join(self.dir_cache, common.utf8(file).decode('utf-8'))
				img_dest = os.path.join(self.dir_merge, utilities.ItemHash(img_source) + utilities.ImageType(img_source))
				xbmcvfs.copy(img_source, img_dest)


	def _folderSize(self, start_path):
		total_size = 0
		for dirpath, dirnames, filenames in os.walk(start_path):
			for f in filenames:
				fp = os.path.join(dirpath, f)
				total_size += os.path.getsize(fp)
		return total_size


	def _resdir(self, artist):
		CacheName = utilities.ItemHash(artist)
		resdir = xbmc.translatePath('special://profile/addon_data/%s/data/%s/' % (common.AddonId(), CacheName,)).decode('utf-8')
		utilities.CheckPath(resdir)
		return resdir


	def _isempty(self, name):
		return True if name is None or name == '' or name.strip() == '' else False


	def onPlayBackStopped(self):
		common.debug('Player stopped, call closing process sequence')
		self._cleanupsignal = True


	def onPlayBackEnded(self):
		common.debug('Player ended, call closing process sequence')
		self._cleanupsignal = True


if __name__ == "__main__":
	MediaSlideshow()
