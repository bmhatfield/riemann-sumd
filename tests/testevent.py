import sys
sys.path.append("lib")

import unittest

import event

import bernhard

class TestEvent(unittest.TestCase):
    def setUp(self):
        self.riemann = bernhard.Client(host='localhost', transport=bernhard.UDPTransport)
        self.ttl_multiplier = 2

    def test_add(self):
        e = event.Events()
        
        e.add(service="servicename",
            state="statename",
            description="description", 
            ttl=60,
            tags=["a", "b"],
            metric=2.2,
            ttl_multiplier=self.ttl_multiplier)

        storedevent = e.events[0]
        self.assertTrue(len(e.events) == 1)
        self.assertEqual(storedevent['metric'], 2.2)
        self.assertEqual(storedevent['service'], "servicename")
        self.assertEqual(storedevent['state'], "statename")
        self.assertEqual(storedevent['description'], "description")
        self.assertEqual(storedevent['ttl'], 60 * self.ttl_multiplier)
        self.assertEqual(storedevent['tags'], ["a", "b"])

    def test_send(self):
        e = event.Events()

        e.add(service="servicename",
            state="statename",
            description="description", 
            ttl=60,
            tags=["a", "b"],
            metric=2.2,
            ttl_multiplier=self.ttl_multiplier)

        self.assertEqual(len(e.events), 1)
        e.send(self.riemann)
        self.assertEqual(len(e.events), 0)
