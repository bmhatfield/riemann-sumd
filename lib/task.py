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

import time

class Task():
	def __init__(self, name, ttl):
		log.info("Creating task: '%s' with TTL of %ss" % (name, ttl))
		self.events = event.Events()
		self.name = name
		self.ttl = ttl
		self.tags = []
		self.timings = [1]

	def add_tags(self, tags):
		if type(tags) == type(str()):
			self.tags.append(tags)
		elif type(tags) == type(list()):
			self.tags.extend(tags)

	def add_timing(self, value, limit=5):
		log.debug("Task %s took %ss" % (self.name, value))
		self.timings.append(value)
		del self.timings[:-limit]

	def skew(self):
		return sum(self.timings)/len(self.timings)

	def start(self):
		log.debug("Starting task: '%s' with TTL of %ss" % (self.name, self.ttl))
		self.start_time = time.time()
		self.run()

	def get_events(self):
		self.join()
		self.end_time = time.time()
		self.add_timing(self.end_time - self.start_time)

		return self.events


class PythonTask(Task):
	def __init__(self, name, ttl, arg):
		Task.__init__(self, name, ttl)
		self.module = arg

	def run(self):
		# TODO: Not yet built. Needs dynamic module/class loading
		pass

	def join(self):
		#self.events.add(service=self.name, state=state, description=description, ttl=self.ttl, tags=self.tags)
		pass


class CloudKickTask(Task):
	def __init__(self, name, ttl, arg):
		Task.__init__(self, name, ttl)
		self.url = arg

	def request(self, url, q):
		try:
			log.debug("Starting web request to '%s'" % (url))
			resp = requests.get(url)
			q.put(resp.json(), timeout=self.skew() * 2)
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
			json_result = self.q.get(timeout=self.skew() * 2)
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
