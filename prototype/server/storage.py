import prototype.server.config as config
import proto.job_pb2 as pb2
import sqlite3


class TaskStorage(object):
    def get_task_result(self, task_id):
        raise NotImplementedError()

    def set_task_result(self, task_id, result):
        raise NotImplementedError()


_INIT_DATABASE = r'''
CREATE TABLE IF NOT EXISTS tasks(
  task_id TEXT PRIMARY KEY,
  task_result BLOB
);
'''

_GET_TASK_RESULT = r'''
SELECT task_id, task_result 
FROM tasks
WHERE task_id=?
'''

_SET_TASK_RESULT = r'''
INSERT INTO tasks
VALUES (?, ?)
'''


class TaskStorageSqlite(TaskStorage):
    def __init__(self):
        self.conn = sqlite3.connect(config.SQLITE_PATH)

    def __del__(self):
        self.conn.close()

    @staticmethod
    def init_database():
        conn = sqlite3.connect(config.SQLITE_PATH)
        conn.execute(_INIT_DATABASE)
        conn.commit()
        conn.close()

    def get_task_result(self, task_id):
        c = self.conn.cursor()
        c.execute(_GET_TASK_RESULT, (task_id,))
        row = c.fetchone()
        if row is None:
            raise KeyError('task_id not found')
        result = pb2.CompletedJob()
        result.ParseFromString(row[1])
        return result

    def set_task_result(self, task_id, result):
        result_bytes = result.SerializeToString()
        c = self.conn.cursor()
        c.execute(_SET_TASK_RESULT, (task_id, result_bytes))
        self.conn.commit()
