import time
import numpy as np


def timed(func):
    def wrapper(self, *args, **kwargs):
        t1 = time.perf_counter()
        result = func(self, *args, **kwargs)
        t2 = time.perf_counter()
        print(f'execution time {t2-t1:.3f} seconds')
        return result
    return wrapper


@timed
def append_list(reps):
    foo = []
    for number in range(reps):
        foo.append(number)
    return foo


@timed
def append_comp(reps):
    foo = []
    [foo.append(i) for i in range(reps)]
    return foo


@timed
def extend_list(reps):
    foo = []
    foo.extend([i for i in range(reps)])
    return foo


@timed
def extend_tup(reps):
    foo = []
    foo.extend((i for i in range(reps)))
    return foo


@timed
def fill_array(reps):
    foo = np.zeros(reps)
    for i in range(reps):
        foo[i] = i
    return foo


repetitions = 1000

