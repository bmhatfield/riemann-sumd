# Import task_queueing library
import threading

import logging
log = logging.getLogger(__name__)


class TaskRunner(threading.Thread):
    def __init__(self, task_queue, event_queue, enable_threads):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.event_queue = event_queue
        self.enable_threads = enable_threads
        self.daemon = True

    def enqueue_events(self, events):
        if len(events) > 0:
            log.debug("Sending %s events..." % (len(events)))

            while len(events) > 0:
                event = events.pop(0)
                log.debug("Event: %s" % (event.dict()))
                self.event_queue.put(event, block=True)
        else:
            log.warning("Enqueue events called with no events to send.")

    def run(self):
        while self.enable_threads:
            log.debug("EventSender %s: waiting for a task..." % (self.name))
            task = self.task_queue.get(block=True)

            if task == "exit":
                log.debug("%s: received 'exit' event" % (self.name))
                break

            try:
                log.debug("%s: Waiting for events from '%s'" % (self.name, task.name))

                events = task.drain()

                log.debug("%s: Waiting complete - attempting to send events - %s" % (self.name, task.name))

                self.enqueue_events(events)
            except Exception as e:
                log.error("Exception sending events from '%s': %s" % (task.name, str(e)))

            log.debug("%s: Events sent - %s" % (self.name, task.name))
            task.locked = False
            self.task_queue.task_done()
