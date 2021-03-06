# -*- coding: utf-8 -*-

import uuid
import pickle
import simplejson

from .utils import atomic_push


class Job(object):
    """
    The item which get pushed to the queue.
    """

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
    """
    Queue which handles queue operation against redis.
    """

    def __init__(self, redis_db, queue_name):
        self.queue_id = 'camoteq:%s' % queue_name
        self.queue_index_id = 'camoteq:index:%s' % queue_name
        self.queue_pubsub_id = 'camoteq:pubsub:%s' % queue_name
        self.redis_db = redis_db

    def push(self, item):
        """
        Push an item to the queue, store the item's index
        and return job object and its 1 based position.
        """
        id = str(uuid.uuid4())
        job = Job(id, item)
        index = atomic_push(self.redis_db,
                            self.queue_id,
                            pickle.dumps(job))

        # set the index of the newly pushed job
        self.redis_db.hset(self.queue_index_id, id, index)

        # increment 1-based position
        job.position = index + 1

        # publish push
        self.redis_db.publish(
            self.queue_pubsub_id,
            simplejson.dumps({'type': 'PUSH', 'job_id': job.id}))

        return job

    def pop(self):
        """
        Pop the first item in the queue and return it.
        """
        # pop a job from the queue
        pickled_job = self.redis_db.lpop(self.queue_id)
        if not pickled_job:
            return None

        # deserialize the job from queue
        job = pickle.loads(pickled_job)

        # delete the job's index
        self.redis_db.hdel(self.queue_index_id, job.id)

        # get all existing index keys and shift the keys using a transaction
        keys = self.redis_db.hkeys(self.queue_index_id)
        pipe = self.redis_db.pipeline()
        for key in keys:
            pipe.hincrby(self.queue_index_id, key, amount=-1)
        pipe.execute()

        # publish pop
        self.redis_db.publish(
            self.queue_pubsub_id,
            simplejson.dumps({'type': 'POP', 'job_id': job.id}))

        return job

    def clear(self):
        """
        Removes all the jobs in the queue.
        """
        while self.pop():
            pass

    def pop_job_by_position(self, position):
        """
        Pop job in queue that is in the `position`.
        """
        # get job from given position
        job = self.get_job_by_position(position)

        # get job index
        job_index = self.redis_db.hget(self.queue_index_id, job.id)

        # delete the job's index
        self.redis_db.hdel(self.queue_index_id, job.id)

        # get all keys whos index are <= job_index
        keys = self.redis_db.hgetall(self.queue_index_id)

        # delete job from queue
        pipe = self.redis_db.pipeline()
        pipe.lset(self.queue_id, job_index, None)  # mark to be deleted
        pipe.lrem(self.queue_id, -1, None)  # delete it

        # shift keys
        for key, index in keys.items():
            if index >= job_index:
                pipe.hincrby(self.queue_index_id, key, amount=-1)

        pipe.execute()

        return job

    def subscribe(self):
        """
        Return pubsub object where consumers can listen for events.
        """
        pubsub = self.redis_db.pubsub()
        pubsub.subscribe(self.queue_pubsub_id)
        return pubsub

    def size(self):
        """
        Return number of jobs in queue.
        """
        return self.redis_db.llen(self.queue_id)

    def update_job_position(self, job):
        """
        Fetch index of a job and update the job's position
        in-place and at the same time returns the same job.
        """
        if not isinstance(job, Job) or not job.id:
            raise Exception("Invalid Job")
        job.position = self.get_position_by_id(job.id)
        return job

    def get_position_by_id(self, job_id):
        """
        Fetch position using job id.
        """
        index = self.redis_db.hget(self.queue_index_id, job_id)
        return -1 if not index else int(index) + 1

    def get_job_by_position(self, position):
        """
        Fetch job at the 1 based position specified.
        """
        pickled_job = self.redis_db.lindex(self.queue_id, position - 1)
        if pickled_job:
            return pickle.loads(pickled_job)
        else:
            return None

    def __unicode__(self):
        return '<CamoteQueue %s>' % self.queue_id
