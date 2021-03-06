import argparse
import grpc
import time
import proto.blackbox_server_pb2 as server_pb2
import proto.blackbox_variable_pb2 as variable_pb2
import proto.job_pb2 as job_pb2
import proto.blackbox_server_pb2_grpc as pb_grpc


def run_task(stub, task_name, binary_path, variable_names, variable_ranges, algorithm):
    def request_generator(binary_path, variable_names, variable_ranges, algorithm):
        request = server_pb2.NewTaskRequest()
        request.job.optimization_job.algorithm = algorithm
        for i, variable_range in enumerate(variable_ranges):
            blackbox_variable = variable_pb2.BlackboxVariableMetadata()
            blackbox_variable.name = variable_names[i]
            blackbox_variable.direct_input.SetInParent()
            if isinstance(variable_range[0], int):
                blackbox_variable.integer_variable.l = variable_range[0]
                blackbox_variable.integer_variable.r = variable_range[1]
            elif isinstance(variable_range[0], float):
                blackbox_variable.continuous_variable.l = variable_range[0]
                blackbox_variable.continuous_variable.r = variable_range[1]
            else:
                blackbox_variable.categorical_variable.categories[:] = variable_range
            request.job.optimization_job.task_variables.append(blackbox_variable)
        yield request

        with open(binary_path, 'rb') as f:
            data = f.read(4096*1024)
            request = server_pb2.NewTaskRequest()
            request.body.chunk = data
            yield request
    print('Optimizing %s with %s variables via %s algorithm' % (task_name, str(variable_ranges),
                                                                job_pb2.Algorithm.Name(algorithm)))
    new_task_response = stub.NewTask(request_generator(binary_path, variable_names, variable_ranges, algorithm))
    task_id = new_task_response.task_id

    while True:
        request = server_pb2.GetTaskResultRequest()
        request.task_id = task_id
        try:
            response = stub.GetTaskResult(request)
            break
        except grpc.RpcError as e:
            status_code = e.code()
            if status_code != grpc.StatusCode.UNAVAILABLE:
                raise e
    completed_job = response.job
    print('Task completed. Final result: %f' % completed_job.optimization_job.result)
    for variable in completed_job.optimization_job.variables:
        if variable.HasField('integer_value'):
            value = variable.integer_value.value
        elif variable.HasField('continuous_value'):
            value = variable.continuous_value.value
        else:
            value = variable.categorical_value.value
        print('Variable %s = %s' % (variable.name, str(value)))


def run_sin_1d(stub):
    run_task(stub, 'sin_1d', 'prototype/examples/sin_1d.py', ['x'], [(-10.0, 10.0)], job_pb2.Algorithm.RANDOM_SEARCH)
    run_task(stub, 'sin_1d', 'prototype/examples/sin_1d.py', ['x'], [(-10.0, 10.0)], job_pb2.Algorithm.SIMULATED_ANNEALING)


def run_rosenbrock_2d(stub):
    run_task(stub, 'rosenbrock_2d', 'prototype/examples/rosenbrock_2d.py', ['x', 'y'], [(-100.0, 100.0), (-100.0, 100.0)],
             job_pb2.Algorithm.RANDOM_SEARCH)
    run_task(stub, 'rosenbrock_2d', 'prototype/examples/rosenbrock_2d.py', ['x', 'y'], [(-100.0, 100.0), (-100.0, 100.0)],
             job_pb2.Algorithm.SIMULATED_ANNEALING)


def run_calculator(stub):
    run_task(stub, 'calculator', 'prototype/examples/calculator.py',
             ['operation', 'x', 'y'], [['plus', 'minus', 'mul'], (-10, 10), (-10, 10)],
             job_pb2.Algorithm.RANDOM_SEARCH)
    run_task(stub, 'calculator', 'prototype/examples/calculator.py',
             ['operation', 'x', 'y'], [['plus', 'minus', 'mul'], (-10, 10), (-10, 10)],
             job_pb2.Algorithm.SIMULATED_ANNEALING)


def main():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb_grpc.BlackboxStub(channel)

    run_sin_1d(stub)
    run_rosenbrock_2d(stub)
    run_calculator(stub)


if __name__ == '__main__':
    main()
