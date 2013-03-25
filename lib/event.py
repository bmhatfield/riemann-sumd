# Riemann client library, depends on protobufs
# https://github.com/banjiewen/bernhard
import bernhard

# For determining hostname
import socket

class Event():
	def __init__(self, service, state, description, ttl, metric=None, hostname=socket.gethostname()):
		self.event = {}
		self.event['service'] = service
		self.event['state'] = state
		self.event['description'] = description
		self.event['ttl'] = ttl
		self.event['hostname'] = hostname
		
		if metric is not None:
			self.event['metric'] = metric

	def send(self, client):
		client.send(self.event)