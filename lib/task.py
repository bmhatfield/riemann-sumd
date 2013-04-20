import logging
log = logging.getLogger(__name__)

# Events, for Task
import event

# Subprocess, for NagiosTask
import subprocess
import shlex

# Multiprocessing, for PythonTask
import multiprocessing

# Requests, for CloudKickTask
import requests
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

import time

class Task():
    def __init__(self, name, ttl):
        log.info("Creating task: '%s' with TTL of %ss" % (name, ttl))
        self.events = event.Events()
        self.name = name
        self.ttl = ttl
        self.tags = set()
        self.timings = [0.75]

    def add_tags(self, tags):
        if type(tags) == type(str()) or type(tags) == type(int()):
            self.tags.add(tags)
        elif type(tags) == type(list()):
            for tag in tags:
                self.tags.add(tag)

    def add_timing(self, value, keep=5):
        log.debug("Task %s took %0.2fs" % (self.name, value))
        self.timings.append(value)
        del self.timings[:-keep]

    def skew(self):
        return sum(self.timings)/len(self.timings)

    def start(self):
        log.info("Starting task: '%s' (usually takes %0.2fs)" % (self.name, self.skew()))
        self.start_time = time.time()
        self.run()

    def get_events(self):
        self.join()
        self.end_time = time.time()
        self.add_timing(self.end_time - self.start_time)

        return self.events


class CloudKickTask(Task):
    def __init__(self, name, ttl, arg):
        Task.__init__(self, name, ttl)
        self.url = arg

    def request(self, url, q):
        try:
            log.debug("Starting web request to '%s'" % (url))
            resp = requests.get(url)
            q.put(resp.json(), timeout=(self.ttl * 0.3))
        except Exception as e:
            log.error("Exception during request method of CloudKickTask '%s'\n%s" % (self.name, str(e)))

    def run(self):
        try:
            self.q = multiprocessing.Queue()
            self.proc = multiprocessing.Process(target=self.request, args=(self.url, self.q))
            self.proc.start()
        except Exception as e:
            log.error("Exception starting CloudKickTask '%s'\n%s" % (self.name, str(e)))

    def join(self):
        try:
            json_result = self.q.get(timeout=(self.ttl * 0.3))
            self.proc.join()

            log.debug('CloudKickTask: Processing %s metrics' % (len(json_result['metrics'])))
            for metric in json_result['metrics']:
                self.events.add(
                    service=metric['name'],
                    state=metric['state'],
                    metric=metric['value'],
                    description="Warn threshold: %s, Error threshold: %s" % (metric['warn_threshold'], metric['error_threshold']),
                    ttl=self.ttl,
                    tags=self.tags
                )
        except Exception as e:
            log.error("Exception joining CloudKickTask '%s'\n%s" % (self.name, str(e)))


class NagiosTask(Task):
    exitcodes = {
        0: 'ok',
        1: 'warn',
        2: 'critical',
        3: 'unknown'
    }

    def __init__(self, name, ttl, arg, shell=False):
        Task.__init__(self, name, ttl)
        self.raw_command = arg
        self.command = shlex.split(arg)
        self.use_shell = shell

    def run(self):
        try:
            self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=self.use_shell)
        except Exception as e:
            log.error("Exception running task '%s':\n%s" % (self.name, str(e)))

    def join(self):
        try:
            stdout, sterr = self.process.communicate()
            description = self.raw_command + "\n" + stdout
            returncode = self.process.returncode

            if returncode in self.exitcodes:
                state = self.exitcodes[returncode]
            else:
                state = 'unknown'

            self.events.add(service=self.name, state=state, description=description, ttl=self.ttl, tags=self.tags)
        except Exception as e:
            log.error("Exception joining task '%s':\n%s" % (self.name, str(e)))
