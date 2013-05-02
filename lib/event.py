# For determining hostname
import socket

import logging
log = logging.getLogger(__name__)

class Events():
    def __init__(self):
        self.events = []

    def add(self, service, state, description, ttl, tags=None, metric=None, attributes=None, host=None, ttl_multiplier=2):
        event = {}
        event['service'] = service
        event['state'] = state
        event['description'] = description
        event['ttl'] = ttl * ttl_multiplier

        if tags is not None:
            event['tags'] = tags

        if metric is not None:
            event['metric'] = metric

        if attributes is not None:
            event['attributes'] = attributes

        if host is None:
          event['host'] = socket.gethostname()
        else:
          event['host'] = host

        self.events.append(event)
        log.debug("Event added: %s" % (event))

    def send(self, client):
        if len(self.events) > 0:
            log.debug("Sending %s events..." % (len(self.events)))
            while len(self.events) > 0:
                event = self.events.pop(0)
                try:
                    client.send(event)
                except socket.error:
                    log.error("Unable to send event '%s' to %s:%s" % (event['service'], client.host, client.port))
        else:
            log.warning("Send called on event object with no events to send.")
