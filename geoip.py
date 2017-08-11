#
# !locate [nick ...]       Do a geoip look up for the given nicknames
# !geoip [host/ip ...]     Do a geoip look up for the given ips or hosts
#

import json, urllib
from halibot import HalModule, HalConfigurer

class GeoIP(HalModule):

	class Configurer(HalConfigurer):
		def configure(self):
			self.optionString('endpoint', prompt='API Endpoint', default='https://freegeoip.net/json/')

	class NoHostnameException(Exception):
		pass

	def init(self):
		pass

	def queryHost(self, ip):
		endpoint = self.config['endpoint']
		rq = urllib.request.urlopen(endpoint + ip)
		return json.loads(rq.read())

	def queryNick(self, nick, agent):
		if hasattr(agent, 'whois'):
			hostname = agent.whois(nick)['hostname']
			if '/' in hostname: # Invalid in hostnames
				raise GeoIP.NoHostnameException()
			try:
				return self.queryHost(hostname)
			except urllib.error.HTTPError as e:
				raise GeoIP.NoHostnameException()
		else:
			raise GeoIP.NoHostnameException()
		return None

	def formatQuery(self, name, q):
		if q != None:
			# Format the result in a human-readable way
			arr = [n for n in [q['city'], q['region_name'], q['country_name']] if n != '']
			return name + ' is located in ' + ', '.join(arr)
		else:
			return 'Cannot locate ' + name

	def receive(self, msg):
		args = [a for a in msg.body.split(' ') if a != '']

		if len(args) > 1:
			if args[0] == '!locate':
				if len(args) == 1:
					args.append(msg.author)
				for name in args[1:]:
					originObj = msg.origin.split('/')[0] # TODO probably should have a message function for this

					try:
						q = self.queryNick(name, self._hal.objects[originObj])
						self.reply(msg, body=self.formatQuery(name, q))
					except GeoIP.NoHostnameException as e:
						self.reply(msg, body='Cannot retrieve the hostname for ' + name)

			if args[0] == '!geoip':
				if len(args) > 1:
					for host in args[1:]:
						try:
							q = self.queryHost(host)
							self.reply(msg, body=self.formatQuery(host, q))
						except urllib.error.HTTPError as e:
							self.reply(msg, body='Cannot retrieve the location of ' + host)
				else:
					self.reply(msg, body='The !geoip command requires an argument')

