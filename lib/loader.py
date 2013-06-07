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
        'json': task.JSONTask,
        'cloudkick': task.HTTPJSONTask,
        'http_json': task.HTTPJSONTask
    }

    required_fields = ['service', 'type', 'arg']

    def __init__(self, path, pattern):
        Loader.__init__(self, path, pattern)
        self.parse()

    def load_tasks(self, additional_tags=None):
        tasks = []
        for config in self.configs:
            for field in self.required_fields:
                if field not in config:
                    log.error('Task missing required field %s' % (field))
                    continue

            if config['type'] in self.task_types:
                # Creates a new task of type 'config['type']'
                t = self.task_types[config['type']](config)

                if additional_tags:
                    t.tags.union(set(additional_tags))

                tasks.append(t)
            else:
                log.error("Task of type '%s' not supported!" % (config['type']))

        return tasks


class TagLoader(Loader):
    def __init__(self, path, pattern):
        Loader.__init__(self, path, pattern)
        self.parse()

    def load_tags(self):
        tags = []
        for tag in self.configs:
            if type(tag['tag']) == type(str()):
                tags.append(tag['tag'])
            elif type(tag['tag']) == type(list()):
                tags.extend(tag['tag'])

        return tags
