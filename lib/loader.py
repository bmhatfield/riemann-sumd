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
        'python': task.PythonTask,
        'cloudkick': task.CloudKickTask
    }

    def __init__(self, path, pattern):
        Loader.__init__(self, path, pattern)
        self.parse()

    def load_tasks(self, additional_tags=None):
        tasks = []
        for task in self.configs:
            for field in ['service', 'type', 'ttl', 'arg']:
                if not field in task:
                    log.error('Task found but missing field %s' % (field))
                    continue

            if task['type'] in self.task_types:
                t = self.task_types[task['type']](name=task['service'], ttl=task['ttl'], arg=task['arg'])

                if additional_tags is not None:
                    t.add_tags(additional_tags)

                if 'tags' in task:
                    t.add_tags(task['tags'])

                tasks.append(t)

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
