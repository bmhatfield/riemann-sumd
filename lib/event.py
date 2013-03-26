# For determining hostname
import socket

import logging
log = logging.getLogger(__name__)

class Events():
	def __init__(self):
		self.events = []

	def add(self, service, state, description, ttl, tags=None, metric=None, host=socket.gethostname()):
		event = {}
		event['service'] = service
		event['state'] = state
		event['description'] = description
		event['ttl'] = ttl
		event['host'] = host
		
		if tags is not None:
			event['tags'] = tags

		if metric is not None:
			event['metric'] = metric

		self.events.append(event)
		log.debug("Event added: %s" % (event))

	def send(self, client):
		log.debug("Sending %s events..." % (len(self.events)))
		while len(self.events) > 0:
			event = self.events.pop(0)
			try:
				client.send(event)
			except socket.error:
				log.error("Unable to send event '%s' to %s:%s" % (event['service'], client.host, client.port))

	