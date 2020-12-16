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
		# read and load plugins
		for cls in ContentProvider.__subclasses__():
			try:
				plugin = cls()
				module = str(cls.__name__).lower()
				if (module == 'local' or common.any2bool(common.setting(module))) and not self.PROVIDERS.has_key(module):
					self.PROVIDERS[module] = plugin
					common.debug('Loading plugin [' + module + ']')
			except BaseException as be:
				common.error('Unexpected error while loading [%s] plugin: %s' %(str(cls),str(be)))
		# process variables
		self.__LastPlayingFile = None
		self.__ProcessRunning = False


	def execute(self):
		if not self.PROVIDERS:
			common.error("No data provider detected")
		else:
			if not self._setInitProcess():
				self._setInitWorkflow()
				while not xbmc.abortRequested and self._isSlideshowEnabled:
					if xbmc.Player().isPlayingAudio() and self._isPlaybackChanged() and not self.__ProcessRunning:
						self.process(True)
					xbmc.sleep(3000)
			else:
				self._setProperty("SlideshowAddon.Resume", "True")
				common.debug('Script already running, no additional instance is needed')
		common.debug('%s v%s has been terminated' % (common.AddonName(), common.AddonVersion()))


	def process(self, trigger=False):
		self.__ProcessRunning = True
		try:
			self._runPropertiesReset()
			self._runDirCleaning(self.__MergeDir)
			self._setLastPlayingFile()
			if trigger:
				self._runSlideshowCollection()
				self._runCacheTrimming()
		except BaseException as be:
			common.error("Error processing slideshow workflow: %s" % str(be))
			if common.istrace:
				traceback.print_exc()
		self.__ProcessRunning = False


	def _setInitProcess(self):
		params = {}
		try:
			if len(sys.argv) >= 2:
				params = dict(arg.split("=") for arg in sys.argv[1].split("&"))
		except Exception as ex:
			common.error('Unexpected error while parsing arguments: %s' % str(ex))
		self.__WID = params.get("windowid", "12006")
		self.__Window = xbmcgui.Window(int(self.__WID))
		common.debug("Parameter 'Window ID' is set to %s" % self.__WID)
		self.ADDON_PROPERTY = "Window(%s).Property(%s)" % (self.__WID, "SlideshowAddon")
		self.ADDON_PROPERTY_RUNNING = "Window(%s).Property(%s)" % (self.__WID, "SlideshowAddon.Running")
		self.ADDON_PROPERTY_RESUME = "Window(%s).Property(%s)" % (self.__WID, "SlideshowAddon.Resume")
		return self._isSlideshowEnabled


	def _setInitWorkflow(self):
		# get settings
		self.__BIOLANGUAGE = common.getAddonSetting("biography_language")
		self.__RESTRICTCACHE = common.setting("restrict_cache")
		self.__MAXCACHESIZE = common.any2int(common.setting("max_cache_size")) * 1000000
		# define workflow resources (paths)
		self.__RootDir = xbmc.translatePath(common.AddonProfile()).decode('utf-8')
		utilities.CheckPath(os.path.join(self.__RootDir, ''))
		self.__DataDir = xbmc.translatePath('special://profile/addon_data/%s/data' % common.AddonId()).decode('utf-8')
		utilities.CheckPath(os.path.join(self.__DataDir, ''))
		self.__MergeDir = xbmc.translatePath('special://profile/addon_data/%s/merge' % common.AddonId()).decode('utf-8')
		utilities.CheckPath(os.path.join(self.__MergeDir, ''))
		self.__TempDir = xbmc.translatePath('special://profile/addon_data/%s/temp' % common.AddonId()).decode('utf-8')
		utilities.CheckPath(os.path.join(self.__TempDir, ''))
		# mark workflow process as started
		self._setProperty("SlideshowAddon", self.__RootDir)
		self._setProperty("SlideshowAddon.Running", "True")
		# initialize workflow variables
		self.__LastTimeCacheTrim = 0
		self.__LastTimeSlideshowSwitch = 0
		self.__LastPlayingFile = None


	def _runSlideshowCollection(self):
		artistsArray = self._getArtistNames()
		artistsCount = len(artistsArray)
		artistsIndex = 0
		for artist in artistsArray:
			if self._isPlaybackChanged():
				return
			if artist is None or artist == '':
				continue
			common.debug("Start collecting slideshow for '%s'" % str(artist))
			artistsIndex += 1
			cacheFound = False
			cacheAdded = False
			self.__InfoDir = self._resdir(artist)
			common.debug('Info directory is %s' % self.__InfoDir)
			self.__CacheDir = self._resdir(artist)
			common.debug('Cache directory is %s' % self.__CacheDir)
			if artistsIndex == 1:
				common.debug('Downloading artist albums and biography..')
				self._getArtistDetails(artist)
			common.debug('Downloading artist images..')
			cachelist = xbmcvfs.listdir(self.__CacheDir)
			cachelist_str = ''.join(str(e) for e in cachelist)
			for file in cachelist[1]:
				if file.lower().endswith('tbn') or file.lower().endswith('jpg') or file.lower().endswith('jpeg') or file.lower().endswith('gif') or file.lower().endswith('png'):
					cacheFound = True
					break
			if cacheFound:
				common.debug('Found artist cache, use it for slideshow!')
				self._setSkinSlideshow(self.__CacheDir)
			for url in self._getArtistImages(artist):
				if self._isPlaybackChanged():
					return
				common.debug('Checking URL: ' + url)
				dstpath = utilities.ItemHashWithPath(url, self.__CacheDir)
				shwpath = utilities.ItemHashWithPath(url, self.__MergeDir)
				_, checkfilename = os.path.split(dstpath)
				if not (checkfilename in cachelist_str):
					urlDownload = self._getDownload(url, shwpath, dstpath)
					if not cacheFound and urlDownload:
						self._setSkinSlideshow(self.__MergeDir, self.__CacheDir)
					elif cacheFound and urlDownload and not cacheAdded:
						self._cache2merge()
						self._setSkinSlideshow(self.__CacheDir, self.__MergeDir)
					cacheAdded |= urlDownload
				time.sleep(1)
			if artistsCount > 1 and not cacheAdded:
				self._cache2merge()
			if artistsIndex == artistsCount and artistsCount > 1:
				self._setSkinSlideshow(self.__MergeDir)
			else:
				self._setSkinSlideshow(self.__CacheDir)
		time.sleep(1)
		common.debug('Finished to download slideshow resources')


	def _getDownload(self, url, shwpath, dstpath):
		if not xbmc.abortRequested:
			tmpimg = os.path.join(self.__TempDir, xbmc.getCacheThumbName(url))
			common.debug('Define temporary image: ' + tmpimg)
			if xbmcvfs.exists(tmpimg):
				utilities.DeleteFile(tmpimg)
			urldata = common.urlcall(url, output='binary')
			if urldata:
				success = utilities.WriteFile(urldata, tmpimg)
				common.debug('Downloaded %s to %s' % (url, tmpimg))
			else:
				success = False
			if not success:
				return False
			if xbmcvfs.Stat(tmpimg).st_size() > 999:
				extension = utilities.ImageType(tmpimg)
				if not xbmcvfs.exists(dstpath + extension):
					common.debug("Copying '%s' to '%s'" % (tmpimg, shwpath + extension))
					xbmcvfs.copy(tmpimg, shwpath + extension)
					common.debug("Moving '%s' to '%s'" % (tmpimg, dstpath + extension))
					xbmcvfs.rename(tmpimg, dstpath + extension)
					return True
				else:
					common.debug('Image already exists, deleting temporary file')
					utilities.DeleteFile(tmpimg)
					return False
			else:
				utilities.DeleteFile(tmpimg)
				return False


	def _getArtistDetails(self, artist):
		biography = ''
		params = {}
		params['infodir'] = self.__InfoDir
		params['lang'] = self.__BIOLANGUAGE
		params['artist'] = artist
		for key in self.PROVIDERS.iterkeys():
			common.debug('Checking provider [%s] for biography..' % key)
			params['getall'] = common.getAddonSetting(key + "_all")
			params['clientapikey'] = common.getAddonSetting(key + "_apikey")
			found = self.PROVIDERS[key].getBiography(params)
			if found is not None and found and len(found) > len(biography):
				common.debug('Stored new biography from provider [%s]' % key)
				biography = found
		self._setProperty("SlideshowAddon.Biography", biography)
		albums = []
		params = {}
		params['infodir'] = self.__InfoDir
		params['lang'] = self.__BIOLANGUAGE
		params['artist'] = artist
		for key in self.PROVIDERS.iterkeys():
			common.debug('Checking provider [%s] for album information..' % key)
			params['getall'] = common.getAddonSetting(key + "_all")
			params['clientapikey'] = common.getAddonSetting(key + "_apikey")
			found = self.PROVIDERS[key].getAlbumList(params)
			if found is not None and len(found) > len(albums):
				common.debug('Got album list from provider [%s]' % key)
				albums = found
		for idx, item in enumerate(albums):
			self._setProperty("SlideshowAddon.%d.AlbumName" % (idx + 1), item[0])
			self._setProperty("SlideshowAddon.%d.AlbumThumb" % (idx + 1), item[1])
			self._setProperty("SlideshowAddon.%d.AlbumYear" % (idx + 1), item[2])
			self._setProperty("SlideshowAddon.%d.AlbumGenre" % (idx + 1), item[3])
		self._setProperty("SlideshowAddon.AlbumCount", str(len(albums)))


	def _getArtistImages(self, artist):
		images = []
		params = {}
		params['lang'] = self.__BIOLANGUAGE
		params['artist'] = artist
		params['infodir'] = self.__InfoDir
		params['exclusionsfile'] = os.path.join(self.__CacheDir, "_exclusions.nfo")
		for key in self.PROVIDERS.iterkeys():
			common.debug('Checking provider [%s] for images..' % key)
			params['getall'] = common.getAddonSetting(key + "_all")
			params['clientapikey'] = common.getAddonSetting(key + "_apikey")
			plist = self.PROVIDERS[key].getImageList(params)
			if plist is not None:
				common.debug('Got images from provider [%s]' % key)
				images.extend(plist)
		return images


	def _getArtistNames(self):
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
				featuring = self._getFeaturedArtists(titleTag)
			if featuring is not None and len(featuring) > 0:
				common.debug('Adding featuring artists in the list: %s' % str(featuring))
				artists.extend(featuring)
			common.debug('Found the following artists: %s' % str(artists))
		return artists


	def _getFeaturedArtists(self, data):
		replace_regex = re.compile(r"ft\.", re.IGNORECASE)
		split_regex = re.compile(r"feat\.", re.IGNORECASE)
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


	def _setSkinSlideshow(self, dir1=None, dir2=None):
		if (dir1 is None or dir1 == '' or not os.path.isdir(dir1) or dir1 == self.__RootDir) and (dir2 is None or dir2 == '' or not os.path.isdir(dir2)):
			common.debug('Set root slideshow to ' + self.__RootDir)
			self._setProperty("SlideshowAddon", self.__RootDir)
			self.__LastTimeSlideshowSwitch = time.time()
		elif dir1 is not None and dir1 != '' and os.path.isdir(dir1) and (dir2 is None or dir2 == '' or not os.path.isdir(dir2)):
			if dir1 != self._skinSlideshow:
				while time.time() - self.__LastTimeSlideshowSwitch < 10:
					time.sleep(1)
				common.debug('Set slideshow to ' + dir1)
				self._setProperty("SlideshowAddon", dir1)
				self.__LastTimeSlideshowSwitch = time.time()
			elif dir1 == self._skinSlideshow and dir1 == self.__CacheDir:
				self._setProperty("SlideshowAddon", self.__MergeDir)
				while time.time() - self.__LastTimeSlideshowSwitch < 10:
					time.sleep(1)
				self._setProperty("SlideshowAddon", dir1)
				common.debug('Set force slideshow to ' + dir1)
				self.__LastTimeSlideshowSwitch = time.time()
			elif dir1 == self._skinSlideshow and dir1 == self.__MergeDir:
				self._setProperty("SlideshowAddon", self.__CacheDir)
				while time.time() - self.__LastTimeSlideshowSwitch < 10:
					time.sleep(1)
				self._setProperty("SlideshowAddon", dir1)
				common.debug('Set force slideshow to ' + dir1)
				self.__LastTimeSlideshowSwitch = time.time()
		elif dir1 is not None and dir1 != '' and os.path.isdir(dir1) and dir2 is not None and dir2 != '' and os.path.isdir(dir2):
			if time.time() - self.__LastTimeSlideshowSwitch > 10:
				if dir1 != self._skinSlideshow:
					common.debug('Set alternate slideshow to ' + dir1)
					self._setProperty("SlideshowAddon", dir1)
					self.__LastTimeSlideshowSwitch = time.time()
				elif dir2 != self._skinSlideshow:
					common.debug('Set alternate slideshow to ' + dir2)
					self._setProperty("SlideshowAddon", dir2)
					self.__LastTimeSlideshowSwitch = time.time()


	def _runPropertiesReset(self):
		common.debug('Resetting skin properties')
		self._setProperty("SlideshowAddon", self.__RootDir)
		self._setProperty("SlideshowAddon.Biography")
		prevAlbumCount = self._infolabel("Window(%s).Property(%s)" % (self.__WID, "SlideshowAddon.AlbumCount"))
		if prevAlbumCount is not None and prevAlbumCount != '':
			for idx in range(int(prevAlbumCount)):
				self._setProperty("SlideshowAddon.%d.AlbumName" % (idx + 1))
				self._setProperty("SlideshowAddon.%d.AlbumThumb" % (idx + 1))
				self._setProperty("SlideshowAddon.%d.AlbumYear" % (idx + 1))
				self._setProperty("SlideshowAddon.%d.AlbumGenre" % (idx + 1))
			self._setProperty("SlideshowAddon.AlbumCount")


	def _runDirCleaning(self, dir):
		if dir == self._skinSlideshow:
			self._setSkinSlideshow()
		common.debug('Cleaning directory: %s' % dir)
		try:
			_, oldfiles = xbmcvfs.listdir(dir)
		except BaseException as e:
			common.error('Unexpected error while getting directory list: %s' % str(e))
			oldfiles = []
		for oldfile in oldfiles:
			if not oldfile.endswith('.nfo'):
				utilities.DeleteFile(os.path.join(dir, oldfile.decode('utf-8')))


	def _runCacheTrimming(self):
		if self.__RESTRICTCACHE and self.__MAXCACHESIZE is not None:
			now = time.time()
			cache_trim_delay = 0  # delay time is in seconds
			if now - self.__LastTimeCacheTrim > cache_trim_delay:
				common.debug('Trimming the cache down to %s bytes' % self.__MAXCACHESIZE)
				cache_root = xbmc.translatePath('special://profile/addon_data/%s/data/' % common.AddonId()).decode('utf-8')
				folders, fls = xbmcvfs.listdir(cache_root)
				folders.sort(key=lambda x: os.path.getmtime(os.path.join(cache_root, x)), reverse=True)
				cachesize = 0
				firstfolder = True
				for folder in folders:
					if self._isPlaybackChanged():
						break
					cachesize = cachesize + self._folderSize(os.path.join(cache_root, folder))
					common.debug('Looking at folder %s cache size is now %s' % (folder, cachesize))
					if cachesize > self.__MAXCACHESIZE and not firstfolder:
						self._runDirCleaning(os.path.join(cache_root, folder))
						common.debug('Deleted files in folder %s' % folder)
					firstfolder = False
				self.__LastTimeCacheTrim = now


	def _isPlaybackChanged(self):
		if common.any2bool(self._infolabel(self.ADDON_PROPERTY_RESUME)):
			self._setProperty("SlideshowAddon.Resume")
			self.__LastPlayingFile = None
			return True
		elif xbmc.Player().isPlayingAudio():
			try:
				nowPlayingFile = xbmc.Player().getPlayingFile()
				if str(nowPlayingFile).startswith("pipe://") or str(nowPlayingFile).startswith("pvr://"):
					nowPlayingFile = xbmc.Player().getMusicInfoTag().getArtist() + " - " + xbmc.Player().getMusicInfoTag().getTitle() + ".raw"
			except:
				nowPlayingFile = None
		else:
			nowPlayingFile = None
		common.trace('Evaluating playback content: %s' %nowPlayingFile)
		return nowPlayingFile != self.__LastPlayingFile


	def _setLastPlayingFile(self):
		if xbmc.Player().isPlayingAudio():
			try:
				self.__LastPlayingFile = xbmc.Player().getPlayingFile()
				if str(self.__LastPlayingFile).startswith("pipe://") or str(self.__LastPlayingFile).startswith("pvr://"):
					self.__LastPlayingFile = xbmc.Player().getMusicInfoTag().getArtist() + " - " + xbmc.Player().getMusicInfoTag().getTitle() + ".raw"
			except:
				self.__LastPlayingFile = None
		else:
			self.__LastPlayingFile = None


	def _setProperty(self, property_name, value=""):
		try:
			self.__Window.setProperty(property_name, value)
			common.trace('Setting %s to value %s' % (property_name, value))
		except BaseException as e:
			common.error("Exception: Couldn't set property %s to value %s: %s" % (property_name, value, str(e)))


	@property
	def _skinSlideshow(self):
		return self._infolabel(self.ADDON_PROPERTY)


	@property
	def _isSlideshowEnabled(self):
		return common.any2bool(self._infolabel(self.ADDON_PROPERTY_RUNNING))


	def _cache2merge(self):
		cachelist = xbmcvfs.listdir(self.__CacheDir)
		for file in cachelist[1]:
			if file.lower().endswith('tbn') or file.lower().endswith('jpg') or file.lower().endswith('jpeg') or file.lower().endswith('gif') or file.lower().endswith('png'):
				img_source = os.path.join(self.__CacheDir, common.utf8(file).decode('utf-8'))
				img_dest = os.path.join(self.__MergeDir, utilities.ItemHash(img_source) + utilities.ImageType(img_source))
				xbmcvfs.copy(img_source, img_dest)


	def _folderSize(self, start_path):
		total_size = 0
		for dirpath, dirnames, filenames in os.walk(start_path):
			for f in filenames:
				fp = os.path.join(dirpath, f)
				total_size += os.path.getsize(fp)
		return total_size


	def _infolabel(self, item):
		try:
			infolabel = xbmc.getInfoLabel(item)
		except:
			infolabel = ''
		return infolabel


	def _resdir(self, theartist):
		CacheName = utilities.ItemHash(theartist)
		resdir = xbmc.translatePath('special://profile/addon_data/%s/data/%s/' % (common.AddonId(), CacheName,)).decode('utf-8')
		utilities.CheckPath(resdir)
		return resdir


	def _isempty(self, name):
		return True if name is None or name == '' or name.strip() == '' else False


	def onPlayBackStarted(self):
		if xbmc.Player().isPlayingAudio():
			self.process(True)
		elif not xbmc.Player().isPlayingAudio() and self.__LastPlayingFile is not None:
			self.process(False)


	def onPlayBackStopped(self):
		if self.__LastPlayingFile is not None:
			self.process(False)


if __name__ == "__main__":
	slideshow = MediaSlideshow()
	slideshow.execute()
