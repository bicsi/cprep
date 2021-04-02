
__CONFIG = None


def load(data: dict):
    global __CONFIG
    __CONFIG = data.copy()


def get(path: str, default=None):
    ret = __CONFIG
    for part in path.split('.'):
        ret = ret[part]
    return ret