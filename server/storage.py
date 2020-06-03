import proto.job_pb2 as job_pb2
import server.config as config

import os
import psycopg2


_INITIALIZE_DATABASE_SQL = r'''
CREATE TABLE IF NOT EXISTS jobs (
  job_id VARCHAR(64) PRIMARY KEY,
  job_data BYTEA,
  job_result BYTEA,
  evaluation_job_origin_id VARCHAR(64),
  assigned_to VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS clients (
  client_id VARCHAR(64) PRIMARY KEY,
  client_heartbeat_time TIMESTAMP WITH TIME ZONE
);
'''

_ADD_JOB_SQL = r'''
INSERT INTO jobs (job_id, job_data)
VALUES (%s, %s);
'''

_ADD_EVALUATION_JOB_SQL = r'''
INSERT INTO jobs (job_id, job_data, evaluation_job_origin_id)
VALUES (%s, %s, %s);
'''

_UPDATE_CLIENT_HEARTBEAT_TIME_SQL = r'''
INSERT INTO clients (client_id, client_heartbeat_time)
VALUES (%s, current_timestamp)
ON CONFLICT(client_id) DO UPDATE
SET client_heartbeat_time=current_timestamp;
'''

_GET_COUNT_OF_ACTIVE_CLIENTS_SQL = r'''
SELECT COUNT(*) FROM clients
WHERE client_heartbeat_time >= current_timestamp - make_interval(secs := %s);
'''

_ASSIGN_JOB_TO_CLIENT_SQL = r'''
UPDATE jobs
SET assigned_to = %s
WHERE job_id = (
    SELECT job_id
    FROM jobs
    WHERE assigned_to IS NULL
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *
'''

_COMPLETE_JOB_SQL = r'''
UPDATE jobs
SET job_result = %s
WHERE job_id = %s
'''

_GET_JOB_SQL = r'''
SELECT job_id, job_data, job_result, assigned_to
FROM jobs
WHERE job_id = %s
'''

_PURGE_DONE_JOBS_SQL = r'''
DELETE FROM jobs j1
USING jobs j2
WHERE
    j1.evaluation_job_origin_id = j2.job_id AND
    j2.job_result IS NOT NULL
'''

_REASSIGN_LOST_JOBS_SQL = r'''
UPDATE jobs
SET assigned_to=NULL
FROM clients
WHERE
    clients.client_id=jobs.assigned_to AND
    jobs.job_result IS NULL AND
    client_heartbeat_time < current_timestamp - make_interval(secs := %s)
'''


class ServerStorage(object):
    def __init__(self):
        self.conn = psycopg2.connect(
            user=config.DATABASE_USER,
            password=config.DATABASE_PASSWORD,
            host=config.DATABASE_HOST,
            database=config.DATABASE_NAME
        )
        self.conn.autocommit = True

    def __del__(self):
        self.conn.close()

    @staticmethod
    def initialize_database():
        with psycopg2.connect(
            user=config.DATABASE_USER,
            password=config.DATABASE_PASSWORD,
            host=config.DATABASE_HOST,
            database=config.DATABASE_NAME
        ) as conn:
            cur = conn.cursor()
            cur.execute(_INITIALIZE_DATABASE_SQL)
            conn.commit()

    def add_job(self, job):
        job_id = job.job_id
        job_data = job.SerializeToString()
        cur = self.conn.cursor()
        if job.HasField('evaluation_job'):
            cur.execute(_ADD_EVALUATION_JOB_SQL, (job_id, job_data, job.evaluation_job.evaluation_job_id))
        else:
            cur.execute(_ADD_JOB_SQL, (job_id, job_data))

    def update_client_heartbeat_time(self, client_id):
        cur = self.conn.cursor()
        cur.execute(_UPDATE_CLIENT_HEARTBEAT_TIME_SQL, (client_id,))

    def get_job(self, client_id):
        cur = self.conn.cursor()
        cur.execute(_ASSIGN_JOB_TO_CLIENT_SQL, (client_id,))
        row = cur.fetchone()
        if row is None:
            return None
        job = job_pb2.Job()
        job.ParseFromString(row[1].tobytes())
        return job

    def complete_job(self, completed_job):
        cur = self.conn.cursor()
        job_id = completed_job.job_id
        job_data = completed_job.SerializeToString()
        cur.execute(_COMPLETE_JOB_SQL, (job_data, job_id))

    def save_job_file_data(self, job_id, block_iter):
        job_path = os.path.join(config.DATA_FOLDER, job_id)
        with open(job_path, 'wb') as f:
            for block in block_iter:
                f.write(block.body.chunk)

    def get_job_file_data(self, job_id):
        job_path = os.path.join(config.DATA_FOLDER, job_id)
        with open(job_path, 'rb') as f:
            yield f.read(4096*1024)

    def get_completed_job(self, job_id):
        cur = self.conn.cursor()
        cur.execute(_GET_JOB_SQL, (job_id,))
        row = cur.fetchone()
        if row is None or row[2] is None:
            return None
        completed_job = job_pb2.CompletedJob()
        completed_job.ParseFromString(row[2].tobytes())
        return completed_job

    def purge_done_jobs(self):
        cur = self.conn.cursor()
        cur.execute(_PURGE_DONE_JOBS_SQL)
        return cur.rowcount

    def reassign_lost_jobs(self):
        cur = self.conn.cursor()
        cur.execute(_REASSIGN_LOST_JOBS_SQL, (config.CLIENT_ACTIVE_TIME,))
        return cur.rowcount

    def get_count_of_active_clients(self):
        cur = self.conn.cursor()
        cur.execute(_GET_COUNT_OF_ACTIVE_CLIENTS_SQL, (config.CLIENT_ACTIVE_TIME,))
        return cur.fetchone()[0]
