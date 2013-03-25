# Import queueing library
import threading

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
			log.debug("Checking for events to send...")
			task = self.queue.get(block=True)
			events = task.get_events()
			events.send(self.riemann)
			self.queue.task_done()