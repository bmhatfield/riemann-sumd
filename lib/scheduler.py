import time

import logging
log = logging.getLogger(__name__)

class TaskSchedule():
	def __init__(self):
		self.tasks = []
		log.debug("TaskSchedule created")

	def add(self, task, ttl_skew=0.5):
		offset = ((ttl_skew * task.ttl) - task.skew())
		
		log.debug("Task skew for '%s' is %s" % ( task.name, task.skew()))
		log.info("Scheduling '%s' for %ss from now" % (task.name, offset))

		if task.skew() > (task.ttl * ttl_skew):
			log.warning("Task skew of %s is > %s%% of TTL(%s) for '%s'" % (task.skew(), (ttl_skew*100), task.ttl, task.name))

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