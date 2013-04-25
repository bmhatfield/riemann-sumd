# Import queueing library
import threading

import time

import logging
log = logging.getLogger(__name__)

class EventSender(threading.Thread):
    def __init__(self, queue, riemann_client, enable_threads):
        log.debug("EventSender created")
        threading.Thread.__init__(self)
        self.queue = queue
        self.riemann = riemann_client
        self.enable_threads = enable_threads
        self.daemon = True

    def run(self):
        while self.enable_threads:
            log.debug("EventSender %s: waiting for a task..." % (self.name))
            task = self.queue.get(block=True)

            if task == "exit":
                log.debug("%s: received 'exit' event" % (self.name))
                break

            log.debug("%s: Waiting for events from '%s'" % (self.name, task.name))
            events = task.get_events()

            log.debug("%s: Waiting complete - attempting to send events - %s" % (self.name, task.name))
            events.send(self.riemann)

            log.debug("%s: Events sent - %s" % (self.name, task.name))
            task.locked = False
            self.queue.task_done()