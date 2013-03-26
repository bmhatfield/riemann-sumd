import time

import logging
log = logging.getLogger(__name__)

class TaskSchedule():
	def __init__(self):
		self.tasks = []
		log.debug("TaskSchedule created")

	def add(self, task, ttl_skew=0.9):
		log.info("Scheduling '%s' for %ss from now" % (task.name, (ttl_skew * task.ttl)))
		deadline = time.time() + (ttl_skew * task.ttl)
		self.tasks.append((task, deadline))

	def update(self):
		log.debug("Updating schedule with nearest deadline last (%s items)" % (len(self.tasks)))
		self.tasks.sort(key=lambda task: task[1], reverse=True)

	def next(self):
		task, deadline = self.tasks.pop()
		log.info("Next task is '%s' with deadline of %s" % (task.name, deadline))
		return (task, deadline)

	def ready(self, deadline, grace=3.0):
		now = time.time()
		return (deadline - now) < grace

	def waiting(self):
		self.update()
		return len([t for t in self.tasks if self.ready(t[1])])