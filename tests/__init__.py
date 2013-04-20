import unittest

from testevent import TestEvent
from testloader import TestLoader
from testscheduler import TestScheduler
from testsender import TestSender
from testtask import TestPythonTask, TestCloudKickTask, TestNagiosTask

suites = []

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestEvent))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestLoader))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestScheduler))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestSender))

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestPythonTask))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestCloudKickTask))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestNagiosTask))

sumdTestSuite = unittest.TestSuite(suites)