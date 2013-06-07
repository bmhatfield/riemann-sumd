import sys
sys.path.append("lib")

import unittest

import event


class TestEvent(unittest.TestCase):
    def setUp(self):
        e = event.Event()
        e.ttl = 60
        e.host = "localhost"
        e.tags = ['unittest']
        e.service = "test-service"
        e.state = 'ok'
        e.metric = 42
        e.description = "This is a test description"
        e.attributes = {'contact-email': 'test@tester.com'}
        self.event = e

    def test_dict(self):
        d = self.event.dict()
        self.assertIn('ttl', d)
        self.assertIn('host', d)
        self.assertIn('tags', d)
        self.assertIn('service', d)
        self.assertIn('state', d)
        self.assertIn('metric', d)
        self.assertIn('description', d)
        self.assertIn('attributes', d)