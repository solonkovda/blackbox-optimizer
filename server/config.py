import os


def _get_or_fail(name):
    result = os.environ.get(name)
    if result is None:
        raise AttributeError('%s env variable is not set' % name)
    return result


DATA_FOLDER = _get_or_fail('DATA_FOLDER')

DATABASE_NAME = _get_or_fail('DATABASE_NAME')
DATABASE_USER = _get_or_fail('DATABASE_USER')
DATABASE_PASSWORD = _get_or_fail('DATABASE_PASSWORD')
DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')

GARBAGE_WAIT_TIME = 5  # 1 minute
CLIENT_ACTIVE_TIME = 20  # 5 minutes.
