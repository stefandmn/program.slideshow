# -*- coding: utf-8 -*-

import os
import sys
import json
import imghdr
import common

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc

if hasattr(sys.modules["__main__"], "xbmcvfs"):
	xbmc = sys.modules["__main__"].xbmcvfs
else:
	import xbmcvfs


def CheckPath(path, create=True):
	common.trace('Checking for %s' % path)
	if not xbmcvfs.exists(path):
		if create:
			common.trace('%s does not exist, creating it' % path)
			xbmcvfs.mkdirs(path)
			return True
		else:
			common.trace('%s does not exist' % path)
			return False
	else:
		common.trace('%s exists' % path)
		return True


def DeleteFile(filename):
	if xbmcvfs.exists(filename):
		try:
			xbmcvfs.delete(filename)
			common.trace('Deleting file %s' % filename)
		except IOError:
			common.error('Unable to delete %s' % filename)
			return False
		except Exception as e:
			common.error('Unknown error while attempting to delete %s: %s' % (filename, e))
			return False,
		return True
	else:
		common.trace('%s does not exist' % filename)
		return False


def ReadFile(filename):
	if xbmcvfs.exists(filename):
		try:
			thefile = xbmcvfs.File(filename, 'r')
		except:
			thefile = open(filename, 'r')
		try:
			data = thefile.read()
			thefile.close()
		except IOError:
			common.error('Unable to read data from ' + filename)
			return None
		except Exception as e:
			common.error('Unknown error while reading data from ' + filename + ": %s" % e)
			return None
		return data
	else:
		common.trace('%s does not exist' % filename)
		return None


def WriteFile(data, filename):
	if type(data).__name__ == 'unicode':
		data = data.encode('utf-8')
	try:
		thefile = xbmcvfs.File(filename, 'wb')
	except:
		thefile = open(filename, 'wb')
	try:
		thefile.write(data)
		thefile.close()
		common.trace('Successfully wrote data to ' + filename)
		return True
	except IOError as e:
		common.trace('Unable to write data to ' + filename + ": " % e)
		return False
	except Exception as e:
		common.trace('Unknown error while writing data to ' + filename + ": %s" % e)
		return False


def ItemHash(item):
	return xbmc.getCacheThumbName(item).replace('.tbn', '')


def ItemHashWithPath(item, thepath):
	thumb = xbmc.getCacheThumbName(item).replace('.tbn', '')
	thumbpath = os.path.join(thepath, thumb.encode('utf-8'))
	return thumbpath


def ImageType(filename):
	try:
		new_ext = '.' + imghdr.what(filename).replace('jpeg', 'jpg')
	except Exception as e:
		new_ext = '.tbn'
	return new_ext
