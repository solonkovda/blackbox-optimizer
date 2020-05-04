import os

DATA_FOLDER = os.environ.get('BLACKBOX_DATA_FOLDER')
if DATA_FOLDER is None:
    raise AttributeError('BLACKBOX_DATA_FOLDER env variable not set')
BINARIES_FOLDER = os.path.join(DATA_FOLDER, 'binaries')
try:
    os.mkdir(BINARIES_FOLDER)
except OSError:
    pass

SQLITE_PATH = os.path.join(DATA_FOLDER, 'database.sqlite')
