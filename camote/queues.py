# -*- coding: utf-8 -*-

import uuid
import pickle

from .utils import atomic_push


class Job(object):
    def __init__(self, id, value):
        self.id = id
        self.value = value
        self.position = -1

    def __setattr__(self, name, value):
        if name == 'position':
            try:
                value = int(value)
            except ValueError:
                raise AttributeError("Position needs to be an integer")
        object.__setattr__(self, name, value)

    def __unicode__(self):
        return '<Job %s>' % self.id


class CamoteQueue(object):
    def __init__(self, redis_db, queue_name):
        self.queue_id = 'camoteq:%s' % queue_name
        self.queue_index_id = 'camoteq:index:%s' % queue_name
        self.redis_db = redis_db

    def push(self, item):
        """ Push an item to the queue, store the item's index
        and return job object and its 1 based position. """
        id = str(uuid.uuid4())
        job = Job(id, item)
        index = atomic_push(self.redis_db,
                            self.queue_id,
                            pickle.dumps(job))
        self.redis_db.hset(self.queue_index_id, id, index)
        job.position = index + 1
        return job

    def pop(self):
        """ Pops the first item in the queue and return it. """
        pickled_job = self.redis_db.lpop(self.queue_id)
        if not pickled_job:
            return None

        job = pickle.loads(pickled_job)
        self.redis_db.hdel(self.queue_index_id, job.id)
        keys = self.redis_db.hkeys(self.queue_index_id)

        # wrap shifting of indexes in a transaction
        pipe = self.redis_db.pipeline()
        for key in keys:
            pipe.hincrby(self.queue_index_id, key, amount=-1)
        pipe.execute()
        return job

    def update_job_position(self, job):
        """ Fetches index of a job and update the job's position
        in-place and at the same time returns the same job. """
        if not isinstance(job, Job) or not job.id:
            raise Exception("Invalid Job")
        job.position = self.get_position_by_id(job.id)
        return job

    def get_position_by_id(self, job_id):
        """ Fetches position using job id. """
        index = self.redis_db.hget(self.queue_index_id, job_id)
        return -1 if not index else int(index) + 1

    def get_job_by_position(self, position):
        """ Fetches job at the 1 based position specified. """
        pickled_job = self.redis_db.lindex(self.queue_id, position - 1)
        if pickled_job:
            return pickle.loads(pickled_job)
        else:
            return None

    def __unicode__(self):
        return '<CamoteQueue %s>' % self.queue_id
