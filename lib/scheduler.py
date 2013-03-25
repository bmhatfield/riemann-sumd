import time

import logging
log = logging.getLogger(__name__)

class TaskSchedule():
	def __init__(self):
		self.tasks = []
		log.debug("TaskSchedule created")

	def add(self, task, ttl_skew=0.9):
		log.debug("Scheduling %s for %ss from now" % (task.name, task.ttl))
		deadline = time.time + (ttl_skew * task.ttl)
		self.tasks.append((task, deadline))

	def update(self):
		log.debug("Sorting schedule")
		self.tasks.sort(key=lambda task: task[1], reverse=True)

	def next(self):
		task, deadline = self.tasks.pop()
		log.debug("Providing task '%s' to caller" % (task.name))
		return (task, deadline)
		

	def ready(self, deadline, grace=3.0):
		now = time.time()
		return (deadline - now) < grace

	def waiting(self):
		self.update()
		return len([t for t in self.tasks if self.ready(t[1])])