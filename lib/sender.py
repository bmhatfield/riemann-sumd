# Import queueing library
import threading

import socket

import logging
log = logging.getLogger(__name__)


class EventSender(threading.Thread):
    def __init__(self, queue, riemann_client, enable_threads):
        threading.Thread.__init__(self)
        self.queue = queue
        self.riemann = riemann_client
        self.enable_threads = enable_threads
        self.daemon = True

    def run(self):
        while self.enable_threads:
            log.debug("EventSender %s: waiting for an event..." % (self.name))
            event = self.queue.get(block=True)

            try:
                log.debug("Sending event: %s" % (event.dict()))
                self.riemann.send(event.dict())
            except socket.error:
                log.error("Unable to send event '%s' to %s:%s" % (event.service, self.riemann.host, self.riemann.port))

            self.queue.task_done()
