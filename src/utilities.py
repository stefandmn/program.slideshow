# -*- coding: utf-8 -*-

import os
import sys
import socket
import imghdr
import commons
import requests

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc

if hasattr(sys.modules["__main__"], "xbmcvfs"):
	xbmc = sys.modules["__main__"].xbmcvfs
else:
	import xbmcvfs


def CheckPath(path, create=True):
	commons.trace('Checking for %s' % path)
	if not xbmcvfs.exists(path):
		if create:
			commons.trace('%s does not exist, creating it' % path)
			xbmcvfs.mkdirs(path)
			return True
		else:
			commons.trace('%s does not exist' % path)
			return False
	else:
		commons.trace('%s exists' % path)
		return True


def DeleteFile(filename):
	if xbmcvfs.exists(filename):
		try:
			xbmcvfs.delete(filename)
			commons.trace('Deleting file %s' % filename)
		except IOError:
			commons.error('Unable to delete %s' % filename)
			return False
		except Exception as e:
			commons.error('Unknown error while attempting to delete %s: %s' % (filename, e))
			return False,
		return True
	else:
		commons.trace('%s does not exist' % filename)
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
			commons.error('Unable to read data from ' + filename)
			return None
		except Exception as e:
			commons.error('Unknown error while reading data from ' + filename + ": %s" % e)
			return None
		return data
	else:
		commons.trace('%s does not exist' % filename)
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
		commons.trace('Successfully wrote data to ' + filename)
		return True
	except IOError as e:
		commons.trace('Unable to write data to ' + filename + ": " % e)
		return False
	except Exception as e:
		commons.trace('Unknown error while writing data to ' + filename + ": %s" % e)
		return False


def SmartUnicode(s):
	if not s:
		return ''
	try:
		if not isinstance(s, basestring):
			if hasattr(s, '__unicode__'):
				s = unicode(s)
			else:
				s = unicode(str(s), 'UTF-8')
		elif not isinstance(s, unicode):
			s = unicode(s, 'UTF-8')
	except:
		if not isinstance(s, basestring):
			if hasattr(s, '__unicode__'):
				s = unicode(s)
			else:
				s = unicode(str(s), 'ISO-8859-1')
		elif not isinstance(s, unicode):
			s = unicode(s, 'ISO-8859-1')
	return s.encode('utf-8')


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
	def __init__(self, returntype='text', headers='', timeout=10):
		self.timeout = timeout
		self.headers = headers
		self.returntype = returntype

	def Get(self, url, **kwargs):
		params, data = self._unpack_args(kwargs)
		return self._urlcall(url, params, '', 'get')

	def Post(self, url, **kwargs):
		params, data = self._unpack_args(kwargs)
		return self._urlcall(url, params, data, 'post')

	def Delete(self, url, **kwargs):
		params, data = self._unpack_args(kwargs)
		return self._urlcall(url, params, data, 'delete')

	def _urlcall(self, url, params, data, urltype):
		urldata = None
		try:
			if urltype == "get":
				urldata = requests.get(url, params=params, timeout=self.timeout, verify=False)
			elif urltype == "post":
				urldata = requests.post(url, params=params, data=data, headers=self.headers, timeout=self.timeout, verify=False)
			elif urltype == "delete":
				urldata = requests.delete(url, params=params, data=data, headers=self.headers, timeout=self.timeout, verify=False)
			commons.debug("The url is [%s], the params are [%s], the data is [%s]" % (urldata.url, str(params), str(data)))
		except requests.exceptions.ConnectionError as e:
			commons.warn('Site unreachable at %s: %s' % (url, str(e)))
		except requests.exceptions.Timeout as e:
			commons.warn('Timeout error while downloading from %s: %s' % (url, str(e)))
		except socket.timeout as e:
			commons.warn('Timeout error while downloading from %s: %s' % (url, str(e)))
		except requests.exceptions.HTTPError as e:
			commons.warn('HTTP Error while downloading from %s: %s' % (url, str(e)))
		except requests.exceptions.RequestException as e:
			commons.warn('Unknown error while downloading from %s: %s' % (url, str(e)))
		if urldata:
			success = True
			commons.debug('Returning URL as ' + self.returntype)
			try:
				if self.returntype == 'text':
					data = urldata.text
				elif self.returntype == 'binary':
					data = urldata.content
				elif self.returntype == 'json':
					data = urldata.json()
			except:
				data = None
				success = False
				commons.warn('Unable to convert returned object to acceptable type')
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
