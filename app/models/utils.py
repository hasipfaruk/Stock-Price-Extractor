import time
from functools import wraps


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        out = func(*args, **kwargs)
        end = time.time()
        return {
            'result': out,
            'time': end-start
        }
    return wrapper