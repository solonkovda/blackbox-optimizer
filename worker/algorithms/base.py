import proto.blackbox_variable_pb2 as blackbox_variable_pb2
import proto.job_pb2 as job_pb2
import proto.jobs_handler_pb2 as jobs_handler_pb2
import worker.config as config

import grpc
import math
import time


def _check_constraint(job_constraint, variables_dict):
    total = 0
    for var_constraint in job_constraint.variable_constraints:
        total += variables_dict[var_constraint.name] * var_constraint.coefficient
    return total < job_constraint.constant_term


class AlgorithmBase(object):
    def __init__(self, client_id, jobs_handler_stub, active_workers):
        self.client_id = client_id
        self.jobs_handler_stub = jobs_handler_stub
        self.start_time = time.time()
        self.total_evaluations = 0
        self.jobs_limit = active_workers * config.MAX_JOBS_PER_ACTIVE_WORKER

    def _check_for_termination(self, job):
        if job.optimization_job.job_parameters.time_limit != 0:
            if self.start_time + job.optimization_job.job_parameters.time_limit < time.time():
                return True
        if job.optimization_job.job_parameters.max_evaluations != 0:
            if self.total_evaluations > job.optimization_job.job_parameters.max_evaluations:
                return True
        return False

    def _start_evaluation_job(self, job, variables_dict):
        for job_constraint in job.optimization_job.job_constraints:
            if not _check_constraint(job_constraint, variables_dict):
                return None

        self.total_evaluations += 1
        new_job = job_pb2.Job()
        new_job.evaluation_job.evaluation_job_id = job.job_id
        new_job.evaluation_job.variables_metadata.extend(job.optimization_job.task_variables)

        for var in job.optimization_job.task_variables:
            new_var = blackbox_variable_pb2.BlackboxVariable()
            new_var.name = var.name
            if var.HasField('continuous_variable'):
                new_var.continuous_value.value = variables_dict[var.name]
            elif var.HasField('integer_variable'):
                new_var.integer_value.value = variables_dict[var.name]
            else:
                new_var.categorical_value.value = variables_dict[var.name]
            new_job.evaluation_job.variables.append(new_var)
        request = jobs_handler_pb2.NewJobRequest()
        request.client_id = self.client_id
        request.job.CopyFrom(new_job)

        response = self.jobs_handler_stub.NewJob(request)
        return response.job_id

    def _get_evaluation_job_result(self, job_id):
        if job_id is None:
            # Job failed to met the task constraints.
            return math.inf
        request = jobs_handler_pb2.GetJobResultRequest()
        request.job_id = job_id
        try:
            response = self.jobs_handler_stub.GetJobResult(request)
        except grpc.RpcError as e:
            status_code = e.code()
            if status_code != grpc.StatusCode.UNAVAILABLE:
                raise e
            return None
        return response.completed_job.evaluation_job.result

    def _parse_job_list(self, job_id_list):
        completed_jobs = []
        remaining_jobs = []
        for job_id, variables in job_id_list:
            result = self._get_evaluation_job_result(job_id)
            if result is not None:
                completed_jobs.append((result, variables))
            else:
                remaining_jobs.append((job_id, variables))
        return completed_jobs, remaining_jobs

    def _wait_for_job_list(self, job_id_list, wait_time=10):
        completed_jobs = []
        for job_id, variables in job_id_list:
            result = self._get_evaluation_job_result(job_id)
            while result is None:
                time.sleep(wait_time)
                result = self._get_evaluation_job_result(job_id)
            completed_jobs.append((result, variables))
        return completed_jobs

    def solve(self, job):
        raise NotImplementedError()
