
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
		_shares, _host, _port, _user, _passwd = hostdetails.split(':', 4)
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
