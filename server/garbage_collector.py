import server.config as config
import server.storage as storage

import threading
import time


class GarbageCollector(threading.Thread):
    def __init__(self):
        super(GarbageCollector, self).__init__()
        self.storage_instance = storage.ServerStorage()

    def run(self):
        while True:
            purged_rows = self.storage_instance.purge_done_jobs()
            if purged_rows > 0:
                print('Garbage collector purged %d completed jobs' % purged_rows)
            fixed_rows = self.storage_instance.reassign_lost_jobs()
            if fixed_rows > 0:
                print('Garbage collector reassigned %d jobs' % fixed_rows)
            time.sleep(config.GARBAGE_WAIT_TIME)
