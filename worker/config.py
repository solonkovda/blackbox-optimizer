import os

DATA_FOLDER = os.environ.get('DATA_FOLDER')
if DATA_FOLDER is None:
    raise AttributeError('DATA_FOLDER env variable is not set')

SERVER_ADDRESS = os.environ.get('SERVER_ADDRESS')
if SERVER_ADDRESS is None:
    raise AttributeError('SERVER_ADDRESS env variable is not set')

HEARTBEAT_TIME = 60
RESPONSE_DELAY = 5

MAX_WORKERS = 4

MAX_JOBS_PER_WORKER = 4
