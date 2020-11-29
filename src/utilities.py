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


class URL:
	def __init__(self, returntype='text', headers=None, timeout=10):
		self.timeout = timeout
		self.headers = headers
		self.returntype = returntype
		self.sslcheck = common.setting("ssl_check")

	def Get(self, url, **kwargs):
		params, data = self._unpack_args(kwargs)
		return self._urlcall(url, params, None, 'GET')

	def Post(self, url, **kwargs):
		params, data = self._unpack_args(kwargs)
		return self._urlcall(url, params, data, 'POST')

	def Delete(self, url, **kwargs):
		params, data = self._unpack_args(kwargs)
		return self._urlcall(url, params, data, 'DELETE')

	def _urlcall(self, url, params, data, urltype):
		urldata = None
		common.debug("Preparing [%s] method, for url [%s], using parameters: %s" % (urltype.upper(), url, str(params)))
		if urltype.lower() == "get":
			urldata = common.urlcall(url, 'GET', fields=params, headers=self.headers, timeout=self.timeout, certver=self.sslcheck)
		elif urltype.lower() == "post":
			urldata = common.urlcall(url, 'POST', fields=params, headers=self.headers, timeout=self.timeout, certver=self.sslcheck)
		elif urltype.lower() == "delete":
			urldata = common.urlcall(url, 'DELETE', fields=params, headers=self.headers, timeout=self.timeout, certver=self.sslcheck)
		if urldata is not None:
			common.debug('Returning URL response as ' + self.returntype)
			try:
				if self.returntype == 'text':
					data = str(urldata)
				elif self.returntype == 'binary':
					data = urldata
				elif self.returntype == 'json':
					data = json.loads(urldata)
				common.debug('URL response: %s ' %(str(data) if self.returntype != 'binary' else "<binary>"))
				success = True
			except:
				data = None
				success = False
				common.warn('Unable to convert returned data to the expected object type')
		else:
			success = False
			data = None
		return success, data

	def _unpack_args(self, kwargs):
		params = kwargs.get('params', {})
		if self.returntype == 'json':
			data = kwargs.get('data', [])
		else:
			data = kwargs.get('data', '')
		return params, data

	def getAgent(self):
		return xbmc.getUserAgent()
