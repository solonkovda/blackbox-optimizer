import proto.blackbox_variable_pb2 as blackbox_variable_pb2
import proto.job_pb2 as job_pb2
import proto.jobs_handler_pb2 as jobs_handler_pb2
import proto.jobs_handler_pb2_grpc as jobs_handler_pb2_grpc
import worker.algorithms.nelder_mead as nelder_mead
import worker.algorithms.opentuner_algorithm as opentuner_algorithm
import worker.algorithms.random_search as random_search
import worker.config as config

import grpc
import sys


def run_worker(job, client_id):
    channel = grpc.insecure_channel(config.SERVER_ADDRESS)
    stub = jobs_handler_pb2_grpc.JobsHandlerStub(channel)
    algorithm = job.optimization_job.algorithm
    if algorithm == job_pb2.Algorithm.RANDOM_SEARCH:
        solver = random_search.RandomSearch(client_id, stub)
    elif algorithm == job_pb2.Algorithm.NELDER_MEAD:
        solver = nelder_mead.NelderMead(client_id, stub)
    else:
        solver = opentuner_algorithm.OpentunerAlgorithm(client_id, stub)

    result, variables_dict = solver.solve(job)

    completed_job = job_pb2.CompletedJob()
    completed_job.job_id = job.job_id
    completed_job.task_id = job.job_id
    completed_job.optimization_job.result = result
    for var in job.optimization_job.task_variables:
        var_value = blackbox_variable_pb2.BlackboxVariable()
        var_value.name = var.name
        if var.HasField('continuous_variable'):
            var_value.continuous_value.value = variables_dict[var.name]
        elif var.HasField('integer_variable'):
            var_value.integer_value.value = variables_dict[var.name]
        else:
            var_value.categorical_value.value = variables_dict[var.name]
        completed_job.optimization_job.variables.append(var_value)

    request = jobs_handler_pb2.CompleteJobRequest()
    request.client_id = client_id
    request.completed_job.CopyFrom(completed_job)
    stub.CompleteJob(request)


if __name__ == '__main__':
    data = sys.stdin.buffer.read()
    job = job_pb2.Job()
    job.ParseFromString(data)
    run_worker(job, sys.argv[1])
