import time

import logging
log = logging.getLogger(__name__)

class TaskSchedule():
	def __init__(self):
		self.tasks = []
		log.debug("TaskSchedule created")

	def add(self, task, ttl_skew=0.95):
		offset = ((ttl_skew * task.ttl) - task.skew())

		log.info("Scheduling '%s' for %ss from now" % (task.name, offset))

		if task.skew() > (task.ttl * 0.5):
			log.warning("Task skew of %s is > 50%% of TTL(%s) for '%s'" % (task.skew(), task.ttl, task.name))
		else:
			log.info("Task skew for '%s' is %s" % ( task.name, task.skew()))

		deadline = time.time() + offset
		self.tasks.append((task, deadline))

	def update(self):
		self.tasks.sort(key=lambda task: task[1], reverse=True)

	def next(self):
		task, deadline = self.tasks.pop()
		log.info("Next task is '%s' scheduled to run in %ss" % (task.name, deadline-time.time()))
		return (task, deadline)

	def ready(self, deadline, grace=1.1):
		now = time.time()
		return (deadline - now) < grace

	def waiting(self):
		self.update()
		return len([t for t in self.tasks if self.ready(t[1])])