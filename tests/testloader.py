import sys
sys.path.append("lib")

import unittest

import loader


class TestLoader(unittest.TestCase):
    def setUp(self):
        self.loader = loader.Loader('tests/fixtures', '*.yml')

    def test_loaded(self):
        self.assertIn('tests/fixtures/basic.yml', self.loader.files)

    def test_parse(self):
        self.loader.parse()

        self.assertIs(list, type(self.loader.configs))
        self.assertEqual(len(self.loader.configs), 1)

        for config in self.loader.configs:
            self.assertIs(dict, type(config))
            self.assertIn('loader', config)
            self.assertEqual('yes!', config['loader'])


class TestTaskLoader(unittest.TestCase):
    def setUp(self):
        self.loader = loader.TaskLoader('tests/fixtures', '*.task')

    def test_tasks(self):
        self.assertIs(list, type(self.loader.load_tasks()))
        self.assertEqual(len(self.loader.load_tasks()), 1)

        for task in self.loader.load_tasks():
            self.assertTrue(hasattr(task, 'name'))
            self.assertTrue(hasattr(task, 'arg'))
            self.assertTrue(hasattr(task, 'ttl'))
            self.assertTrue(hasattr(task, 'tags'))
            self.assertTrue(hasattr(task, 'note'))
            self.assertTrue(hasattr(task, 'ttl_multiplier'))
            self.assertTrue(hasattr(task, 'attributes'))

            self.assertIn('metric', task.config)


class TestTagLoader(unittest.TestCase):
    def setUp(self):
        self.loader = loader.TagLoader('tests/fixtures', '*.tag')

    def test_tasks(self):
        self.assertIs(list, type(self.loader.load_tags()))
        self.assertEqual(len(self.loader.load_tags()), 1)

        for tag in self.loader.load_tags():
            self.assertEqual('tag-list', tag)
