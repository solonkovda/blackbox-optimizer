import proto.blackbox_server_pb2 as pb2
import proto.blackbox_server_pb2_grpc as pb2_grpc
import proto.job_pb2 as job_pb2
import server.garbage_collector as garbage_collector
import server.jobs_handler as jobs_handler
import server.storage as storage

import uuid
from concurrent import futures
import grpc


def _validate_optimization_job_constraints(job, context):
    variables_dict = dict()
    for var in job.optimization_job.task_variables:
        variables_dict[var.name] = var
    for job_constraint in job.optimization_job.job_constraints:
        for var_constraint in job_constraint.variable_constraints:
            if variables_dict[var_constraint.name].HasField('categorical_variable'):
                context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "Categorical variables can't be part of a constraint"
                )


def _validate_optimization_job_algorithm(job, context):
    if job.optimization_job.algorithm == job_pb2.Algorithm.SIMULATED_ANNEALING:
        context.abort(
            grpc.StatusCode.UNIMPLEMENTED,
            'Simulated annealing is not supported'
        )
    if job.optimization_job.algorithm == job_pb2.Algorithm.NELDER_MEAD:
        for var in job.optimization_job.task_variables:
            if not var.HasField('continuous_variable'):
                context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    'NELDER_MEAD algorithm only supports continuous variables'
                )
    if job.optimization_job.algorithm == job_pb2.Algorithm.OPENTUNER:
        for var in job.optimization_job.task_variables:
            if var.HasField('categorical_variable'):
                context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "Opentuner version doesn't support categorical variables"
                )


class BlackboxServer(pb2_grpc.BlackboxServicer):
    def __init__(self):
        super(BlackboxServer, self).__init__()
        self.storage_instance = storage.ServerStorage()
    
    def NewTask(self, request_iter, context):
        job_id = str(uuid.uuid4())
        job = request_iter.next().job
        _validate_optimization_job_algorithm(job, context)
        _validate_optimization_job_constraints(job, context)

        self.storage_instance.save_job_file_data(job_id, request_iter)

        job.job_id = job_id
        self.storage_instance.add_job(job)

        response = pb2.NewTaskResponse()
        response.task_id = job_id
        return response

    def GetTaskResult(self, request, context):
        response = pb2.GetTaskResultResponse()
        completed_job = self.storage_instance.get_completed_job(request.task_id)
        if completed_job is None:
            context.abort(
                grpc.StatusCode.UNAVAILABLE,
                'Task is not completed'
            )
        response.job.CopyFrom(completed_job)
        return response


def main():
    storage.ServerStorage.initialize_database()
    collector_thread = garbage_collector.GarbageCollector()
    collector_thread.start()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_BlackboxServicer_to_server(BlackboxServer(), server)
    jobs_handler.add_jobs_handler_to_server(server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
