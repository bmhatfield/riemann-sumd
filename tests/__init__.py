import unittest

from testevent import TestEvent
from testloader import TestLoader, TestTaskLoader, TestTagLoader
from testscheduler import TestTaskSchedule
from testsender import TestSender
from testtask import TestJSONTask, TestHTTPJSONTask, TestNagiosTask

suites = []

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestEvent))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestLoader))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestTaskLoader))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestTagLoader))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestTaskSchedule))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestSender))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestJSONTask))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestHTTPJSONTask))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestNagiosTask))

sumdTestSuite = unittest.TestSuite(suites)