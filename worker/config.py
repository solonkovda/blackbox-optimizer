import os


def _get_or_fail(name):
    result = os.environ.get(name)
    if result is None:
        raise AttributeError('%s env variable is not set' % name)
    return result


HEARTBEAT_TIME = 10
RESPONSE_DELAY = 5

DATA_FOLDER = _get_or_fail('DATA_FOLDER')
SERVER_ADDRESS = _get_or_fail('SERVER_ADDRESS')
MAX_WORKERS = os.environ.get('MAX_WORKERS', 4)
MAX_JOBS_PER_ACTIVE_WORKER = os.environ.get('MAX_JOBS_PER_ACTIVE_WORKER', 2)

