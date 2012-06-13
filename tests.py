#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import redis
import camote


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

    def test_get_position_by_id(self):
        items = ['iPad', 'Cinema Display', 'Mountain Bike']
        for i, item in enumerate(items):
            job = self.queue.push(item)
            self.assertEqual(self.queue.get_position_by_id(job.id), i + 1)

    def test_invalid_job(self):
        invalid_job = "foobar"
        self.assertRaises(Exception, self.queue.update_job_position, invalid_job)


class JobTest(unittest.TestCase):
    def test_set_position(self):
        job = camote.Job(1, 'some value')
        def _assignment_wrapper(job, new_position):
            job.position = new_position
        self.assertRaises(AttributeError, _assignment_wrapper, job, 'a')


if __name__ == '__main__':
    unittest.main()
