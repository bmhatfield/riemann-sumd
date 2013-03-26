import logging
log = logging.getLogger(__name__)

# Events, for Task
import event

# Subprocess, for NagiosTask
import subprocess
import shlex

# Multiprocessing, for PythonTask
import multiprocessing

import time

class Task():
	def __init__(self, name, ttl):
		log.info("Creating task: '%s' with TTL of %ss" % (name, ttl))
		self.events = event.Events()
		self.name = name
		self.ttl = ttl
		self.tags = []
		self.timings = [0]

	def add_timing(self, value, limit=5):
		self.timings.append(value)
		del self.timings[:-limit]

	def skew(self):
		return sum(self.timings)/len(self.timings)

	def start(self):
		log.info("Starting task: '%s' with TTL of %ss" % (self.name, self.ttl))
		self.start_time = time.time()
		self.run()

	def get_events(self):
		self.join()
		self.end_time = time.time()
		self.add_timing(self.end_time - self.start_time)

		return self.events


class PythonTask(Task):
	def __init__(self, name, ttl, module):
		Task.__init__(self, name, ttl)
		self.module = module

	def run(self):
		pass

	def join(self):
		self.events.add(service=self.name, state=state, description=description, ttl=self.ttl, tags=self.tags)


class NagiosTask(Task):
	exitcodes = {
		0: 'ok',
		1: 'warn',
		2: 'error',
		3: 'unknown'
	}

	def __init__(self, name, ttl, command, shell=False):
		Task.__init__(self, name, ttl)
		self.raw_command = command
		self.command = shlex.split(command)
		self.use_shell = shell

	def run(self):
		try:
			self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=self.use_shell)
		except Exception as e:
			log.error("Exception running task '%s':\n%s" % (self.name, str(e)))

	def join(self):
		stdout, sterr = self.process.communicate()
		description = self.raw_command + "\n" + stdout
		returncode = self.process.returncode

		if returncode in self.exitcodes:
			state = self.exitcodes[returncode]
		else:
			state = 'unknown'

		self.events.add(service=self.name, state=state, description=description, ttl=self.ttl, tags=self.tags)
