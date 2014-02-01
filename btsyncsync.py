#!/usr/bin/env python
"""

Author: Alex Wilson <alex@kbni.net>
Date: 1st Febuary 2014
License: WTFPL (http://www.wtfpl.net/)
Description:
	Tool to aid in syncing shares amongst BitTorrent Sync hosts.
	This tool will compare shares on all defined hosts, and any which are
	in a 'common share' directory (share_dir in the JSON) will be added to
	all other hosts (under their share_dir). It will not actually make the
	directory in the OS, and BitTorrent Sync does not do this for you, but
	this script will dump a mkdir string you can use for that, then re-run
	the script and the shares will then add.

	BitTorrent Sync API is not required (that's kind of the point of this)
	I have no wish to sign up for a special API key

In your ~/.btsyncsync.json:

{
    "host1": {
        "share_dir": "/storage/btsynced",
        "host_port": "192.168.2.250:8888",
        "user_pass": "username:password"
    },
    "host2": {
        "share_dir": "/var/lib/btsynced",
        "host_port": "192.168.2.253:8888",
        "user_pass": "username:password"
    }
}

share_dir is the directory where common shares will be placed.

"""

import sys
import re
import os
import bittorrentsync as bts
import simplejson as json

def shellquote(s): return "'" + s.replace("'", "'\\''") + "'"

if __name__ == "__main__":
	json_file = os.path.join(os.environ['HOME'], '.btsyncsync.json')
	if os.environ.has_key('BTSYNCSYNC_JSON'):
		json_file = os.environ['BTSYNCSYNC_JSON']

	fh = open(json_file, 'r')
	hosts = json.load(fh)
	fh.close()

	print hosts
	sys.exit(0)

	w_host = {}
	distshares = {}

	for hostname, hostdetails in hosts.iteritems():
		_shares = hostdetails['share_dir']
		_host, _port = hostdetails['host_port'].split(':', 2)
		_user, _passwd = hostdetails['user_pass'].split(':', 2)
		sync_obj = bts.BitTorrentSync(user=_user, passwd=_passwd, host=_host, port=_port)
		sync_obj._used_fw_keys = []
		sync_obj._used_ro_keys = []
		sync_obj._folders = []
		sync_obj._needs = []
		sync_obj._shares = _shares
		w_host[hostname] = sync_obj

	for hostname, sync in w_host.iteritems():
		try:
			sync.getToken()
		except bts.urllib2.URLError:
			print "Unable to get token from host '%s' (bad credentials?)" % (hostname,)
			sys.exit(1)

		for folder in sync.getStats()['folders']:
			if folder['name'].find(sync._shares) == 0:
				short_name = os.path.basename(folder['name'])
				secret = folder['secret']
				distshares[short_name] = secret
				sync._folders.append(short_name)

	for hostname, sync in w_host.iteritems():
		for short_name, secret in distshares.iteritems():
			if short_name not in sync._folders:
				sync._needs.append(short_name)

	for hostname, sync in w_host.iteritems():
		if sync._needs:
			shfriendly = []
			for needed in sync._needs:
				fullpath = os.path.join(sync._shares, needed)
				sync.addSyncFolder(fullpath, distshares[needed])
				shfriendly.append(shellquote(fullpath))
			print "on %s, run: mkdir -p %s" % (hostname, ' '.join(shfriendly))
