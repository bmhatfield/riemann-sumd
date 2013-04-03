import unittest

from testevent import TestEvent
from testloader import TestLoader
from testscheduler import TestScheduler
from testsender import TestSender
from testtask import TestTask

suites = []

suites.append(unittest.TestLoader().loadTestsFromTestCase(TestEvent))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestLoader))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestScheduler))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestSender))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestTask))

sumdTestSuite = unittest.TestSuite(suites)