import os
import glob
import yaml

import task

import logging
log = logging.getLogger(__name__)

class Loader():
	def __init__(self, path, pattern):
		filepath = os.path.join(path, pattern)
		log.info("Loading configs from %s" % (filepath))
		self.files = glob.glob(filepath)

	def parse(self):
		self.configs = []

		for f in self.files:
			with open(f) as yf:
				log.debug('YAML Parsing: %s' % (f))
				self.configs.append(yaml.safe_load(yf.read()))

class TaskLoader(Loader):
	task_types = {
		'nagios': task.NagiosTask,
		'python': task.PythonTask
	}

	def __init__(self, path, pattern):
		Loader.__init__(self, path, pattern)
		self.parse()

	def schedule_tasks(self, scheduler):
		for task in self.configs:
			if task['type'] in self.task_types:
				t = self.task_types[task['type']](name=task['service'], ttl=task['ttl'], command=task['command'])
				scheduler.add(t)

class TagLoader(Loader):
	def __init__(self, path, pattern):
		Loader.__init__(self, path, pattern)
		self.parse()

	def add_tags(self, tags):
		for tag in self.configs:
			if type(tag['tag']) == type(str()):
				tags.append(tag['tag'])
			elif type(tag['tag']) == type(list()):
				tags.extend(tag['tag'])
