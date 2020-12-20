# -*- coding: utf-8 -*-

import os
import sys
import json
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
	common.trace('Checking %s' % path, "utilities")
	if not xbmcvfs.exists(path):
		if create:
			common.trace('Not found and try to create it: %s' % path, "utilities")
			xbmcvfs.mkdirs(path)
			return True
		else:
			common.trace('Not found: %s' % path, "utilities")
			return False
	else:
		common.trace('Found: %s' % path, "utilities")
		return True


def DeleteFile(filename):
	if xbmcvfs.exists(filename):
		try:
			xbmcvfs.delete(filename)
			common.trace('Deleting file: %s' % filename, "utilities")
			return True
		except IOError:
			common.error('Unable to delete file: %s' % filename, "utilities")
			return False
		except Exception as e:
			common.error('Unknown error while attempting to delete [%s] file path: %s' % (filename, e), "utilities")
			return False,
	else:
		common.trace('File does not exist: %s' % filename, "utilities")
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
			common.error('Unable to read data from file: %s' %filename, "utilities")
			return None
		except Exception as e:
			common.error('Unknown error while reading data from [%s] file: %s' %(filename, str(e)), "utilities")
			return None
		return data
	else:
		common.trace('File does not exist: %s' %filename, "utilities")
		return None


def WriteFile(data, filename):
	if type(data).__name__ == 'unicode':
		data = data.encode('utf-8')
	elif isinstance(data, dict):
		data = json.dumps(data)
	try:
		thefile = xbmcvfs.File(filename, 'wb')
	except:
		thefile = open(filename, 'wb')
	try:
		thefile.write(data)
		thefile.close()
		common.trace('Successfully wrote data to file: %s' %filename, "utilities")
		return True
	except IOError as e:
		common.error('Unable to write data to [%s] file: %s' %(filename, str(e)), "utilities")
		return False
	except Exception as e:
		common.error('Unknown error while writing data to [%s] file: %s' %(filename, str(e)), "utilities")
		return False


def ItemHash(item):
	return xbmc.getCacheThumbName(item).replace('.tbn', '')


def ItemHashWithPath(item, path):
	thumb = xbmc.getCacheThumbName(item).replace('.tbn', '')
	thumbpath = os.path.join(path, thumb.encode('utf-8'))
	return thumbpath


def ImageType(filepath):
	try:
		ext = str(os.path.splitext(filepath)).replace('jpeg', 'jpg')
	except:
		ext = '.tbn'
	return ext
