import unittest

from testevent import TestEvent
from testloader import TestTaskLoader, TestTagLoader
from testscheduler import TestTaskSchedule
from testsender import TestSender
from testtask import TestJSONTask, TestCloudKickTask, TestNagiosTask

suites = []

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestEvent))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestTaskLoader))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestTagLoader))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestTaskSchedule))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestSender))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestJSONTask))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestCloudKickTask))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestNagiosTask))

sumdTestSuite = unittest.TestSuite(suites)