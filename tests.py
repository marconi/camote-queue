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
            job, initial_position = self.queue.push(item['name'])
            items[i]['job'] = job
            self.assertEqual(initial_position, i + 1)

        for i, item in enumerate(items):
            position = self.queue.get_job_position(item['job'])
            self.assertEqual(position, i + 1)

    def test_pop(self):
        items = [{'name': 'Macbook Pro', 'job': None},
                 {'name': 'iPhone', 'job': None},
                 {'name': 'iMac', 'job': None}]
        for i, item in enumerate(items):
            job, initial_position = self.queue.push(item['name'])
            items[i]['job'] = job

        item1, item2, item3 = items

        # first pop
        job = self.queue.pop()
        popped_position = self.queue.get_job_position(job)
        self.assertEqual(popped_position, None)
        self.assertEqual(self.queue.get_job_position(item1['job']), None)
        self.assertEqual(self.queue.get_job_position(item2['job']), 1)
        self.assertEqual(self.queue.get_job_position(item3['job']), 2)

        # second pop
        job = self.queue.pop()
        popped_position = self.queue.get_job_position(job)
        self.assertEqual(popped_position, None)
        self.assertEqual(self.queue.get_job_position(item1['job']), None)
        self.assertEqual(self.queue.get_job_position(item2['job']), None)
        self.assertEqual(self.queue.get_job_position(item3['job']), 1)

        # third pop
        job = self.queue.pop()
        popped_position = self.queue.get_job_position(job)
        self.assertEqual(popped_position, None)
        self.assertEqual(self.queue.get_job_position(item1['job']), None)
        self.assertEqual(self.queue.get_job_position(item2['job']), None)
        self.assertEqual(self.queue.get_job_position(item3['job']), None)

        # fourth pop
        job = self.queue.pop()
        self.assertEqual(job, None)


if __name__ == '__main__':
    unittest.main()
