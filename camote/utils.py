
def atomic_push(redis_db, queue_id, item):
    """ Push item to queue and get queue updated length in
    one atomic operation by using transaction. """
    pipe = redis_db.pipeline()
    pipe.rpush(queue_id, item)
    pipe.llen(queue_id)
    _, queue_size = pipe.execute()
    return queue_size - 1

def get_queue_size(redis_db, queue_id):
    return redis_db.llen(queue_id)
