#!/usr/bin/env python
"""

Author: Alex Wilson <alex@kbni.net>
Date: 1st Febuary 2014
License: WTFPL (http://www.wtfpl.net/)
Description:
	NOT TO BE CONFUSED WITH OFFICIAL BITTORENT SYNC API!
	These are Python bindings for the Linux BitTorrent Sync webui.
	
"""

import base64
import json
import os
import re
import sys
import time
import urllib2

VALID_PREFS = ["relay", "usetracker", "searchlan", "searchdht", "deletetotrash", "usehosts"]
ALLOW_400_ACTIONS = ["setfolderpref"]

class BitTorrentSync:
	def __init__(self, **kwargs):
		self.cookie = None
		self.token = None
		self.user = kwargs.get('user', os.environ.get('BTS_USER', 'admin'))
		self.passwd = kwargs.get('passwd', os.environ.get('BTS_PASSWD', 'admin'))
		self.host = kwargs.get('host', os.environ.get('BTS_HOST', '127.0.0.1'))
		self.port = int(kwargs.get('port', os.environ.get('BTS_PORT', 8080)))
		self.proto = kwargs.get('proto', os.environ.get('BTS_PROTO', 'http'))

	def getToken(self):
		if not self.token:
			uri = '/gui/token.html'
			self.token = self.request(uri, get_token=True)
		return self.token

	def request(self, uri, allow_400=False, get_token=False):
		full_req = '%s://%s:%d%s' % (self.proto, self.host, self.port, uri)
		
		request = urllib2.Request(full_req)
		base64string = base64.encodestring('%s:%s' % (self.user, self.passwd)).replace('\n', '')
		request.add_header("Authorization", "Basic %s" % base64string)
		if self.cookie:
			request.add_header('cookie', self.cookie.replace('\n',''))
		
		try:
			response = urllib2.urlopen(request)
			result = response.read()

			if get_token:
				self.cookie = response.headers.get('Set-Cookie')
				return re.findall('<div[^>]*>([^>]*)<', result)[0]
			else:
				return json.loads(result)
		
		except urllib2.URLError, e:
			if not allow_400:
				raise urllib2.URLError(e)
				
	def action(self, action, **kwargs):
		uri = '/gui/?token=%s&action=%s&t=%s' % (
			self.getToken(), action, int(time.time()*1000)
		)
		for key, value in kwargs.iteritems():
			uri += '&%s=%s' % (key, urllib2.quote(str(value).encode('utf-8')))
		return self.request(uri, allow_400=action in ALLOW_400_ACTIONS)
	
	def getStats(self):
		return self.action('getsyncfolders')
		
	def generateSecret(self):
		return self.action('generatesecret')
	
	def addSyncFolder(self, name, secret):
		return self.action('addsyncfolder', name=name, secret=secret)
	
	def addSyncFolderForce(self, name, secret):
		return self.action('addsyncfolder', name=name, secret=secret, force=1)

	def getSyncFolders(self):
		return self.action('getsyncfolders')
	
	def removeSyncFolder(self, name, secret):
		return self.action('removefolder', name=name, secret=secret)

	def getHosts(self, name, secret):
		return self.action('getknownhosts', name=name, secret=secret)
	
	def addHost(self, name, secret, addr, port):
		return self.action('addknownhosts', name=name, secret=secret, addr=addr, port=port)
	
	def removeHost(self, name, secret, index):
		return self.action('removeknownhosts', name=name, secret=secret, index=index)
	
	def updateSecret(self, secret, newsecret):
		return self.action('updatesecret', secret=secret, newsecret=newsecret)
	
	def generateInvite(self, name, secret):
		return self.action('generateinvite', name=name, secret=secret)
	
	def generateROInvite(self, name, secret):
		return self.action('generateroinvite', name=name, secret=secret)

	def getUserName(self):
		return self.action('getusername')

	def getOsType(self):
		return self.action('getostype')
	
	def getVersion(self):
		return self.action('getversion')

	def getVersion2(self):
		version = self.getVersion()['version']
		return '%s.%s.%s' % (
			(version & 0xFF000000) >> 24,
			(version & 0x00FF0000) >> 16,
			(version & 0x0000FFFF)
		)

	def getFolderPreferences(self, name, secret):
		return self.action('getfolderpref', secret=secret, name=name)['folderpref']
	
	def setFolderPreferences(self, name, secret, **prefs):
		original_prefs = self.action('getfolderpref', secret=secret, name=name)['folderpref']
		for (key, value) in original_prefs.iteritems():
			if key != 'iswritable' and not key in prefs:
				prefs[key] = value
		return self.action('setfolderpref', secret=secret, name=name, **prefs)

"""
"""

def main_test_alpha():
	bts = BitTorrentSync()
	stats = bts.getStats()
	print stats
	print bts.generateSecret()
	print bts.getUserName()
	print bts.getOsType()
	print bts.getVersion()
	print bts.getVersion2()
	secret = stats['folders'][0]['secret']
	name = stats['folders'][0]['name']
	print bts.setFolderPreferences(name, secret, deletetotrash=0)
	print bts.getFolderPreferences(name, secret)

if __name__ == '__main__':
	main_test_alpha()
