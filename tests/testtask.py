import sys
sys.path.append("lib")

import unittest


class TestTask(unittest.TestCase):
    def setUp(self):
        pass

    def test_add_tag(self):
        pass

    def test_add_timing(self):
        pass

    def test_skew(self):
        pass

    def test_start(self):
        pass

    def test_draing(self):
        pass


class TestJSONTask(TestTask):
    def setUp(self):
        pass


class TestHTTPJSONTask(TestTask):
    def setUp(self):
        # Perhaps start a simple http server with JSON output?
        # Or replay a captured copy of actual JSON output?
        pass


class TestNagiosTask(TestTask):
    def setUp(self):
        # Scaffold up a nagios task that does something silly
        pass
