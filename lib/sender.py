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

	def run(self):
		while self.enable_threads:
			log.debug("EventSender %s: waiting for a task..." % (self.name))
			task = self.queue.get(block=True)

			if task == "exit":
				log.debug("%s: received 'exit' event" % (self.name))
				break

			log.debug("%s: Got task - %s" % (self.name, task.name))
			events = task.get_events()

			log.debug("%s: Sending events - %s" % (self.name, task.name))
			events.send(self.riemann)

			log.debug("%s: sending task complete - %s" % (self.name, task.name))
			self.queue.task_done()