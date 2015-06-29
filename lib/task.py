import logging
log = logging.getLogger(__name__)

import re
import time

# For determining hostname
import socket

# Event
from event import Event

# Subprocess, for NagiosTask
import shlex
import subprocess

# Multiprocessing, for PythonTask
import multiprocessing

# Requests, for CloudKickTask
import requests

# JSON, for JSONTask
import json


# Some module-level constants for definining tasks
DEFAULT_TTL = 60
DEFAULT_HOSTNAME = socket.gethostname()
DEFAULT_MULTIPLIER = 5

SEED_TIMING = 0.5

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
    required_config = ['service', 'arg']

    def __init__(self, config):
        self.config = config

        # Confirm that the passed config object contains required values
        for key in self.required_config:
            if key not in config:
                raise KeyError("Config missing '%s'" % (key))

        self.name = config['service']
        self.arg = config['arg']

        # Handle some common task options and their defaults
        self.ttl_multiplier = config['ttl_multiplier'] if 'ttl_multiplier' in config else DEFAULT_MULTIPLIER
        self.host = config['host'] if 'host' in config else DEFAULT_HOSTNAME
        self.ttl = config['ttl'] if 'ttl' in config else DEFAULT_TTL

        self.attributes = config['attributes'] if 'attributes' in config else {}
        self.tags = set(config['tags']) if 'tags' in config else set()
        self.note = config['note'] if 'note' in config else ""

        # Initialize task internal values
        self.events = []
        self.timings = [SEED_TIMING]
        self.locked = False

        log.info("Creating task: '%s' with TTL of %ss" % (self.name, self.ttl))

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

    def drain(self):
        self.join()
        self.end_time = time.time()
        self.add_timing(self.end_time - self.start_time)

        tevents = []
        while len(self.events) > 0:
            tevents.append(self.events.pop(0))

        # Now that we've got our events, free the task to run again
        self.locked = False
        return tevents


class HTTPJSONTask(Task):
    def __init__(self, config):
        Task.__init__(self, config)
        self.q = multiprocessing.Queue()

    def request(self):
        try:
            log.debug("Starting web request to '%s'" % (self.arg))
            resp = requests.get(self.arg)
            self.q.put(resp.json(), timeout=(self.ttl * 0.3))
        except Exception as e:
            log.error("Exception during request method of CloudKickTask '%s'\n%s" % (self.name, str(e)))

    def run(self):
        try:
            self.proc = multiprocessing.Process(target=self.request)
            self.proc.start()
        except Exception as e:
            log.error("Exception starting CloudKickTask '%s'\n%s" % (self.name, str(e)))

    def join(self):
        try:
            json_result = self.q.get(timeout=(self.ttl * 0.3))
            self.proc.join()

            log.debug('CloudKickTask: Processing %s metrics' % (len(json_result['metrics'])))
            for metric in json_result['metrics']:
                note = metric['note'] if 'note' in metric else self.note
                event = Event()
                event.ttl = self.ttl * self.ttl_multiplier
                event.host = self.host
                event.tags = self.tags
                event.service = metric['name']
                event.state = metric['state']
                event.metric = metric['value']
                event.description = "%s\nWarn threshold: %s, Error threshold: %s" % (note,
                                                                                     metric['warn_threshold'],
                                                                                     metric['error_threshold'])
                if 'attributes' in metric:
                    event.attributes = metric['attributes']

                self.events.append(event)
        except Exception as e:
            log.error("Exception joining CloudKickTask '%s'\n%s" % (self.name, str(e)))
            self.locked = False


class SubProcessTask(Task):
    def __init__(self, config):
        Task.__init__(self, config)

        self.raw_command = self.arg
        self.command = shlex.split(self.arg)
        self.process = None
        self.use_shell = False
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
                if self.process.poll() is None:
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
        1: 'warning',
        2: 'critical',
        3: 'unknown'
    }

    def __init__(self, config):
        SubProcessTask.__init__(self, config)

    def parse_nagios_output(self, stdout):
        # TODO: Be more robust if this fails for any reason
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
                attributes[self.attrprefix + key] = val

            return output, attributes
        else:
            log.warning("Output for task '%s' could not be parsed for perf data: %s" % (self.name, str(parts)))
            return (stdout, None)

    def join(self):
        try:
            stdout, stderr, returncode = SubProcessTask.join(self)

            event = Event()
            event.service = self.name
            event.ttl = self.ttl * self.ttl_multiplier
            event.host = self.host
            event.tags = self.tags
            event.attributes = self.attributes

            output, attributes = self.parse_nagios_output(stdout)
            event.description = "Note: %s\nCommand: %s\nOutput: %s\n" % (self.note, self.raw_command, output)

            if returncode in self.exitcodes:
                event.state = self.exitcodes[returncode]
            else:
                event.state = 'unknown'

            if attributes:
                if 'metric' in self.config and self.config['metric'] in attributes:
                    metric_key = self.config['metric']
                else:
                    metric_key = attributes.keys()[0]

                event.attributes.update(attributes)
                event.metric = float(NUMERIC_REGEX.match(attributes[metric_key]).group(1))

            self.events.append(event)
        except Exception as e:
            log.error("Exception joining task '%s':\n%s" % (self.name, str(e)))


class JSONTask(SubProcessTask):
    def __init__(self, config):
        SubProcessTask.__init__(self, config)

    def join(self):
        try:
            stdout, stderr, returncode = SubProcessTask.join(self)

            try:
                results = json.loads(stdout)
            except Exception as e:
                log.error("Failed to parse JSON. '%s':\n%s" % (self.name, str(e)))
                return

            for result in results:
                for field in ['service', 'state', 'description', 'metric']:
                    if field not in result:
                        log.error("Event missing field '%s'" % (field))
                        continue

                event = Event()
                event.ttl = self.ttl * self.ttl_multiplier
                event.host = self.host
                event.tags = self.tags
                event.attributes = self.attributes

                if "attributes" in result:
                    event.attributes.update(dict((self.attrprefix + name, result["attributes"][name]) for name in result["attributes"]))

                event.service = result['service']
                event.state = result['state']
                event.metric = result['metric']
                event.description = "%s\n%s" % (self.note, result['description'])
                self.events.append(event)
        except Exception as e:
            log.error("Exception joining task '%s':\n%s" % (self.name, str(e)))
