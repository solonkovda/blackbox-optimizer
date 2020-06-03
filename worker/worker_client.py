import proto.jobs_handler_pb2 as pb2
import proto.jobs_handler_pb2_grpc as pb2_grpc
import worker.config as config

import grpc
import os
import subprocess
import threading
import time
import uuid

_shutdown_graceful = False
_shutdown_force = False


def handle_sig(signum, frame):
    global _shutdown_graceful, _shutdown_force
    if not _shutdown_graceful:
        _shutdown_graceful = True
    else:
        _shutdown_force = True


class HeartbeatThread(threading.Thread):
    def __init__(self, server_address, client_id):
        super().__init__()
        self.server_address = server_address
        self.client_id = client_id
        self.running = True
        self.active_workers = 0

    def run(self):
        channel = grpc.insecure_channel(self.server_address)
        stub = pb2_grpc.JobsHandlerStub(channel)
        request = pb2.HeartbeatRequest()
        request.client_id = self.client_id
        while self.running:
            response = stub.Heartbeat(request)
            self.active_workers = response.active_workers
            time.sleep(config.HEARTBEAT_TIME)


class JobProcess(object):
    def __init__(self, stub, client_id, job):
        self.stub = stub
        self.client_id = client_id
        self.job = job
        self.process = None

    @staticmethod
    def create_job_process(stub, client_id, job):
        if job.HasField('evaluation_job'):
            return EvaluationJobProcess(stub, client_id, job)
        else:
            return OptimizationJobProcess(stub, client_id, job)

    def start(self, active_workers):
        raise NotImplementedError()

    def check_status(self):
        if self.process:
            return self.process.poll()
        return None

    def kill(self):
        if self.process:
            self.process.kill()

    def join(self):
        if self.process:
            self.process.join()


class EvaluationJobProcess(JobProcess):
    def _download_task_data(self):
        task_id = self.job.evaluation_job.evaluation_job_id
        completed_task_path = os.path.join(
            config.DATA_FOLDER, task_id + '.completed')
        file_path = os.path.join(
            config.DATA_FOLDER, task_id)
        if os.path.exists(completed_task_path):
            # Task already downloaded, extracting data
            return file_path
        request = pb2.GetJobDataRequest()
        request.client_id = client_id
        request.job_id = task_id

        response = self.stub.GetJobData(request)
        with open(file_path, 'wb') as f:
            for block in response:
                f.write(block.chunk)
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | 0o111)

        with open(completed_task_path, 'wb') as f:
            pass
        return file_path

    def __init__(self, stub, client_id, job):
        super().__init__(stub, client_id, job)
        self.task_binary_path = self._download_task_data()

    def start(self, active_workers):
        p = subprocess.Popen(
            ['worker/evaluator_process', client_id, self.task_binary_path],
            stdin=subprocess.PIPE,
            close_fds=True
        )
        p.stdin.write(self.job.SerializeToString())
        p.stdin.close()
        self.process = p


class OptimizationJobProcess(JobProcess):
    def start(self, active_workers):
        p = subprocess.Popen(
            ['worker/optimization_process', self.client_id, str(active_workers)],
            stdin=subprocess.PIPE,
            close_fds=True
        )
        p.stdin.write(self.job.SerializeToString())
        p.stdin.close()
        self.process = p


def _request_and_start_job(stub, client_id, active_workers):
    request = pb2.GetJobRequest()
    request.client_id = client_id
    try:
        response = stub.GetJob(request)
    except grpc.RpcError as e:
        status_code = e.code()
        if status_code != grpc.StatusCode.UNAVAILABLE:
            raise e
        return None
    job = response.job
    job_process = JobProcess.create_job_process(stub, client_id, job)
    job_process.start(active_workers)
    return job_process


def worker_loop(client_id):
    channel = grpc.insecure_channel(config.SERVER_ADDRESS)
    stub = pb2_grpc.JobsHandlerStub(channel)

    heartbeat_thread = HeartbeatThread(config.SERVER_ADDRESS, client_id)
    heartbeat_thread.start()

    workers = []
    while not _shutdown_graceful:
        current_active_workers = heartbeat_thread.active_workers
        if not current_active_workers:
            time.sleep(config.RESPONSE_DELAY)
            continue
        while len(workers) < config.MAX_WORKERS:
            worker = _request_and_start_job(stub, client_id, current_active_workers)
            if worker is None:
                break
            workers.append(worker)
        remaining_workers = []
        for w in workers:
            status_code = w.check_status()
            if status_code is None:
                remaining_workers.append(w)
            elif status_code != 0:
                # Restarting worker
                w.start(current_active_workers)
                remaining_workers.append(w)
        workers = remaining_workers
        time.sleep(config.RESPONSE_DELAY)

    for w in workers:
        if _shutdown_force:
            w.kill()
        w.join()
    heartbeat_thread.running = False
    heartbeat_thread.join()


if __name__ == '__main__':
    client_id = str(uuid.uuid4())
    print('Worker started, id = %s' % client_id, flush=True)
    worker_loop(client_id)
