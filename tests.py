#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import unittest
import redis
import camote
import threading
import simplejson


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Test')


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.redis_db = redis.StrictRedis()
        self.queue = camote.CamoteQueue(self.redis_db, 'camote')

    def tearDown(self):
        self.redis_db.delete(self.queue.queue_id, self.queue.queue_index_id)

    def test_push(self):
        items = [{'name': 'Macbook Pro', 'job': None},
                 {'name': 'iPhone', 'job': None},
                 {'name': 'iMac', 'job': None}]
        for i, item in enumerate(items):
            job = self.queue.push(item['name'])
            items[i]['job'] = job
            self.assertEqual(job.position, i + 1)

        for i, item in enumerate(items):
            self.queue.update_job_position(item['job'])
            self.assertEqual(item['job'].position, i + 1)

    def test_pop(self):
        items = [{'name': 'Macbook Pro', 'job': None},
                 {'name': 'iPhone', 'job': None},
                 {'name': 'iMac', 'job': None}]
        for i, item in enumerate(items):
            job = self.queue.push(item['name'])
            items[i]['job'] = job

        item1, item2, item3 = items

        # first pop
        job = self.queue.pop()
        self.queue.update_job_position(job)
        self.assertEqual(job.position, -1)
        self.assertEqual(self.queue.update_job_position(item1['job']).position, -1)
        self.assertEqual(self.queue.update_job_position(item2['job']).position, 1)
        self.assertEqual(self.queue.update_job_position(item3['job']).position, 2)

        # second pop
        job = self.queue.pop()
        self.queue.update_job_position(job)
        self.assertEqual(job.position, -1)
        self.assertEqual(self.queue.update_job_position(item1['job']).position, -1)
        self.assertEqual(self.queue.update_job_position(item2['job']).position, -1)
        self.assertEqual(self.queue.update_job_position(item3['job']).position, 1)

        # third pop
        job = self.queue.pop()
        self.queue.update_job_position(job)
        self.assertEqual(job.position, -1)
        self.assertEqual(self.queue.update_job_position(item1['job']).position, -1)
        self.assertEqual(self.queue.update_job_position(item2['job']).position, -1)
        self.assertEqual(self.queue.update_job_position(item3['job']).position, -1)

        # fourth pop
        job = self.queue.pop()
        self.assertEqual(job, None)

    def test_size(self):
        items = [{'name': 'Macbook Pro', 'job': None},
                 {'name': 'iPhone', 'job': None},
                 {'name': 'iMac', 'job': None}]
        for i, item in enumerate(items):
            job = self.queue.push(item['name'])
            items[i]['job'] = job

        self.assertEqual(self.queue.size(), 3)

    def test_get_position_by_id(self):
        items = ['iPad', 'Cinema Display', 'Mountain Bike']
        for i, item in enumerate(items):
            job = self.queue.push(item)
            self.assertEqual(self.queue.get_position_by_id(job.id), i + 1)

    def test_invalid_job(self):
        invalid_job = "foobar"
        self.assertRaises(Exception, self.queue.update_job_position, invalid_job)

    def test_get_job_by_position(self):
        items = ['iPad', 'Cinema Display', 'Mountain Bike']
        for i, item in enumerate(items):
            job = self.queue.push(item)
            position = self.queue.get_position_by_id(job.id)
            self.assertEqual(self.queue.get_job_by_position(position).id, job.id)

    def test_event_subscription(self):

        class SubscriberRunner(threading.Thread):
            def __init__(self, queue):
                super(SubscriberRunner, self).__init__()
                self.subscription = queue.subscribe()

            def run(self):
                for msg in self.subscription.listen():
                    if msg['type'] == 'message':
                        job = simplejson.loads(msg['data'])
                        self.type = job['type']
                        self.job_id = job['job_id']
                        break

        items = [{'name': 'Macbook Pro', 'job': None},
                 {'name': 'iPhone', 'job': None},
                 {'name': 'iMac', 'job': None}]

        # test push
        jobs = []
        runners = []
        for item in items:
            sr = SubscriberRunner(self.queue)
            sr.start()
            runners.append(sr)
            jobs.append(self.queue.push(item['name']))

        for i, runner in enumerate(runners):
            runner.join()
            self.assertEqual(runner.job_id, jobs[i].id)
            self.assertEqual(runner.type, 'PUSH')

        # test pop
        jobs = []
        runners = []
        for __ in range(len(jobs)):
            sr = SubscriberRunner(self.queue)
            sr.start()
            runners.append(sr)
            jobs.append(self.queue.pop())

        for i, runner in enumerate(runners):
            runner.join()
            self.assertEqual(runner.job_id, jobs[i].id)
            self.assertEqual(runner.type, 'POP')

    def test_pop_job_by_position(self):
        items = [{'name': 'Macbook Pro', 'job': None},
                 {'name': 'iPhone', 'job': None},
                 {'name': 'iMac', 'job': None}]
        for i, item in enumerate(items):
            job = self.queue.push(item['name'])
            items[i]['job'] = job

        job = self.queue.pop_job_by_position(2)  # pop iPhone
        self.assertEqual(self.queue.size(), 2)
        self.assertEqual(job.value, 'iPhone')

        keys = self.redis_db.hgetall(self.queue.queue_index_id)

        for key, index in keys.items():
            position = int(index) + 1
            job = self.queue.get_job_by_position(position)
            self.assertEqual(job.id, key)

        job = self.queue.pop_job_by_position(2)  # pop iMac
        self.assertEqual(self.queue.size(), 1)
        self.assertEqual(job.value, 'iMac')

        keys = self.redis_db.hgetall(self.queue.queue_index_id)

        for key, index in keys.items():
            position = int(index) + 1
            job = self.queue.get_job_by_position(position)
            self.assertEqual(job.id, key)

        job = self.queue.pop_job_by_position(1)  # pop Macbook Pro
        self.assertEqual(self.queue.size(), 0)
        self.assertEqual(job.value, 'Macbook Pro')

        keys = self.redis_db.hgetall(self.queue.queue_index_id)
        self.assertEqual(len(keys), 0)


class JobTest(unittest.TestCase):
    def test_set_position(self):
        job = camote.Job(1, 'some value')
        def _assignment_wrapper(job, new_position):
            job.position = new_position
        self.assertRaises(AttributeError, _assignment_wrapper, job, 'a')


if __name__ == '__main__':
    unittest.main()
