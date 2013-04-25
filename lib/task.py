import logging
log = logging.getLogger(__name__)

import re
import time

# Events, for Task
import event

# Subprocess, for NagiosTask
import shlex
import subprocess

# Multiprocessing, for PythonTask
import multiprocessing

# Requests, for CloudKickTask
import requests

# JSON, for JSONTask
import json

# Numeric matcher for parsing Nagios performance data
# create class constant compiled regex, to prevent
# unecessarily recompiling this regex string.
NUMERIC_REGEX = re.compile('([\d.]+)')

# Configure logging for the Requests module, decreasing
# the verbosity even when we are running in a more
# verbose mode otherwise.
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)


class Task():
    def __init__(self, name, ttl):
        log.info("Creating task: '%s' with TTL of %ss" % (name, ttl))
        self.events = event.Events()
        self.name = name
        self.ttl = ttl
        self.tags = set()
        self.timings = [0.75]
        self.locked = False

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
        if not self.locked:
            log.info("Starting task: '%s' (usually takes %0.2fs)" % (self.name, self.skew()))
            self.locked = True
            self.start_time = time.time()
            self.run()
        else:
            raise RuntimeError("Task '%s' is locked - cannot start another." % (self.name))

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


class SubProcessTask(Task):
    def __init__(self, name, ttl, arg, shell=False):
        Task.__init__(self, name, ttl)
        self.raw_command = arg
        self.command = shlex.split(arg)
        self.process = None
        self.use_shell = shell
        self.attrprefix = 'task_'

    def run(self):
        try:
            self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=self.use_shell)
        except Exception as e:
            log.error("Exception running task '%s':\n%s" % (self.name, str(e)))

    def join(self):
        try:
            deadline = self.start_time + (self.ttl * 0.5)
            while deadline > time.time():
                if self.process.poll() == None:
                    time.sleep(0.5)
                else:
                    log.debug("Gathering output from task '%s'" % (self.name))
                    stdout, sterr = self.process.communicate()
                    return stdout, sterr, self.process.returncode
            else:
                log.warning("Deadline expired for task '%s' - force killing" % (self.name))
                self.process.kill()
                self.process.wait()
                log.debug("Subprocess killed for task '%s'" % (self.name))
                return '', '', -127
        except Exception as e:
            log.error("Exception joining task '%s':\n%s" % (self.name, str(e)))


class NagiosTask(SubProcessTask):
    exitcodes = {
     -127: 'timeout',
        0: 'ok',
        1: 'warn',
        2: 'critical',
        3: 'unknown'
    }

    def __init__(self, name, ttl, arg, shell=False):
        SubProcessTask.__init__(self, name, ttl, arg, shell)

    def parse_nagios_output(self, stdout):
        parts = stdout.split("|")
        if len(parts) == 1:
            log.debug("Task '%s' did not return perf data." % (self.name))
            return (parts[0], None)
        elif len(parts) == 2:
            attributes = {}
            output, raw_perf = parts
            log.debug("Task '%s' returned perf data: %s" % (self.name, raw_perf.strip()))
            for item in raw_perf.strip().split(" "):
                key, val = item.split(';')[0].split('=')
                attributes[self.attrprefix + key] = float(NUMERIC_REGEX.match(val).group(1))

            return output, attributes
        else:
            log.warning("Output for task '%s' could not be parsed for perf data: %s" % (self.name, str(parts)))
            return (stdout, None)

    def join(self):
        try:
            metric = None
            state = 'unknown'

            stdout, stderr, returncode = SubProcessTask.join(self)

            if returncode in self.exitcodes:
                state = self.exitcodes[returncode]

            output, attributes = self.parse_nagios_output(stdout)

            if attributes:
                metric = attributes[attributes.keys()[0]]

            self.events.add(service=self.name,
                            state=state,
                            description=self.raw_command + "\n" + output,
                            metric=metric,
                            attributes=attributes,
                            ttl=self.ttl,
                            tags=self.tags)
        except Exception as e:
            log.error("Exception joining task '%s':\n%s" % (self.name, str(e)))


class JSONTask(SubProcessTask):
    def __init__(self, name, ttl, arg, shell=False):
        SubProcessTask.__init__(self, name, ttl, arg, shell)

    def join(self):
        try:
            stdout, stderr, returncode = SubProcessTask.join(self)

            try:
                results = json.loads(stdout)
            except Exception as e:
                log.error("Failed to parse JSON. '%s':\n%s" % (self.name, str(e)))

            for result in results:
                for field in ['service', 'state', 'description', 'metric']:
                    if field not in result:
                        log.error("Event missing field '%s'" % (field))
                        continue

                self.events.add(service=result['service'],
                                state=result['state'],
                                description=result['description'],
                                metric=result['metric'],
                                ttl=self.ttl,
                                tags=self.tags)
        except Exception as e:
            log.error("Exception joining task '%s':\n%s" % (self.name, str(e)))
