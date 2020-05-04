import argparse
import grpc
import time
import prototype.server.proto.blackbox_server_pb2 as server_pb2
import prototype.server.proto.blackbox_variable_pb2 as variable_pb2
import prototype.server.proto.blackbox_server_pb2_grpc as pb_grpc


def run_task(stub, task_name, binary_path, variable_names, variable_ranges, algorithm):
    def request_generator(binary_path, variable_names, variable_ranges, algorithm):
        request = server_pb2.NewTaskRequest()
        request.metadata.algorithm = algorithm
        for i, variable_range in enumerate(variable_ranges):
            blackbox_variable = variable_pb2.BlackboxVariable()
            blackbox_variable.name = variable_names[i]
            blackbox_variable.direct_input.SetInParent()
            if isinstance(variable_range[0], int):
                blackbox_variable.integer_variable.l = variable_range[0]
                blackbox_variable.integer_variable.r = variable_range[1]
            elif isinstance(variable_range[0], float):
                blackbox_variable.continious_variable.l = variable_range[0]
                blackbox_variable.continious_variable.r = variable_range[1]
            else:
                blackbox_variable.categorical_variable.categories[:] = variable_range
            request.metadata.task_variables.append(blackbox_variable)
        yield request

        with open(binary_path, 'rb') as f:
            data = f.read(4096*1024)
            request = server_pb2.NewTaskRequest()
            request.body.chunk = data
            yield request
    print('Optimizing %s with %s variables via %s algorithm' % (task_name, str(variable_ranges),
                                                                server_pb2.NewTaskRequest.Algorithm.Name(algorithm)))
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
    print('Task completed. Final result: %f' % response.result)
    for variable in response.variable_values:
        if variable.HasField('integer_value'):
            value = variable.integer_value.value
        elif variable.HasField('continious_value'):
            value = variable.continious_value.value
        else:
            value = variable.categorical_value.value
        print('Variable %s = %s' % (variable.name, str(value)))


def run_sin_1d(stub):
    run_task(stub, 'sin_1d', 'examples/sin_1d.py', ['x'], [(-10.0, 10.0)], server_pb2.NewTaskRequest.Algorithm.RANDOM_SEARCH)
    run_task(stub, 'sin_1d', 'examples/sin_1d.py', ['x'], [(-10.0, 10.0)], server_pb2.NewTaskRequest.Algorithm.SIMULATED_ANNEALING)


def run_rosenbrock_2d(stub):
    run_task(stub, 'rosenbrock_2d', 'examples/rosenbrock_2d.py', ['x', 'y'], [(-100.0, 100.0), (-100.0, 100.0)],
             server_pb2.NewTaskRequest.Algorithm.RANDOM_SEARCH)
    run_task(stub, 'rosenbrock_2d', 'examples/rosenbrock_2d.py', ['x', 'y'], [(-10.0, 10.0), (-100.0, 100.0)],
             server_pb2.NewTaskRequest.Algorithm.SIMULATED_ANNEALING)


def run_calculator(stub):
    run_task(stub, 'calculator', 'examples/calculator.py',
             ['operation', 'x', 'y'], [['plus', 'minus', 'mul'], (-10, 10), (-10, 10)],
             server_pb2.NewTaskRequest.Algorithm.RANDOM_SEARCH)
    run_task(stub, 'calculator', 'examples/calculator.py',
             ['operation', 'x', 'y'], [['plus', 'minus', 'mul'], (-10, 10), (-10, 10)],
             server_pb2.NewTaskRequest.Algorithm.SIMULATED_ANNEALING)


def main():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb_grpc.BlackboxStub(channel)

    run_sin_1d(stub)
    run_rosenbrock_2d(stub)
    run_calculator(stub)


if __name__ == '__main__':
    main()
