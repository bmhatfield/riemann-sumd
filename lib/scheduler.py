import time

import logging
log = logging.getLogger(__name__)


class TaskSchedule():
    def __init__(self):
        self.tasks = []
        log.debug("TaskSchedule created")

    def add(self, task, max_skew_factor=0.5):
        offset = (task.ttl - task.skew())

        log.debug("Task skew for '%s' is %0.2fs" % (task.name, task.skew()))
        log.debug("Scheduling '%s' for %0.2fs from now" % (task.name, offset))

        if task.skew() > (task.ttl * max_skew_factor):
            log.warning("Task skew of %0.2f is > %s%% of TTL(%s) for '%s'" %
                        (task.skew(), (max_skew_factor * 100), task.ttl, task.name))

        deadline = time.time() + offset
        self.tasks.append((task, deadline))

    def update(self):
        self.tasks.sort(key=lambda task: task[1], reverse=True)

    def next(self):
        task, deadline = self.tasks.pop()
        log.debug("Task '%s' near deadline (scheduled in %0.2fs)" % (task.name, deadline-time.time()))
        return (task, deadline)

    def ready(self, deadline, grace=1.1):
        now = time.time()
        return (deadline - now) < grace

    def waiting(self):
        self.update()
        return len([t for t in self.tasks if self.ready(t[1])])
