import os


def _get_or_fail(name):
    result = os.environ.get(name)
    if result is None:
        raise AttributeError('%s env variable is not set' % name)
    return result


DATA_FOLDER = _get_or_fail('DATA_FOLDER')
SERVER_ADDRESS = _get_or_fail('SERVER_ADDRESS')
HEARTBEAT_TIME = int(os.environ.get('HEARTBEAT_TIME', 60))
RESPONSE_DELAY = int(os.environ.get('RESPONSE_DELAY', 5))
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))
MAX_JOBS_PER_ACTIVE_WORKER = int(os.environ.get('MAX_JOBS_PER_ACTIVE_WORKER', 2))
