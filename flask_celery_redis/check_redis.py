import redis

r = redis.Redis(host='localhost', port=6379, db=0)


def is_redis_available(r):
    try:
        r.ping()
        print("Successfully connected to redis")
    except (redis.exceptions.ConnectionError, ConnectionRefusedError):
        print("Redis connection error!")
        return False
    return True


if is_redis_available(r):
    print("redis is available")
