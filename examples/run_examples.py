import proto.blackbox_server_pb2 as blackbox_server_pb2
import proto.blackbox_server_pb2_grpc as blackbox_server_pb2_grpc
import proto.blackbox_variable_pb2 as blackbox_variable_pb2
import proto.job_pb2 as job_pb2

import argparse
import time
import grpc

_ALGORITHM_CHOICES = [
    'random_search',
    'nelder_mead',
    'opentuner'
]

parser = argparse.ArgumentParser()
parser.add_argument('--server-address',
                    help='Address of the server',
                    default='localhost:50051')
parser.add_argument('--algorithm',
                    help='Algorithm to use',
                    default='random_search',
                    choices=_ALGORITHM_CHOICES)


def _wait_for_task(stub, task_id):
    request = blackbox_server_pb2.GetTaskResultRequest()
    request.task_id = task_id
    while True:
        try:
            response = stub.GetTaskResult(request)
            break
        except grpc.RpcError as e:
            status_code = e.code()
            if status_code != grpc.StatusCode.UNAVAILABLE:
                raise e
        time.sleep(10)
    return response


def request_generator(header, binary_path):
    yield header
    with open(binary_path, 'rb') as f:
        data = f.read(1024*1024)
        r = blackbox_server_pb2.NewTaskRequest()
        r.body.chunk = data
        yield r


def _run_example(stub, path, algorithm, variables):
    print('Running %s' % path)
    print('Variables: %s' % str(variables))
    header = blackbox_server_pb2.NewTaskRequest()
    header.job.optimization_job.algorithm = algorithm
    for name, value in variables.items():
        var = blackbox_variable_pb2.BlackboxVariableMetadata()
        var.name = name
        if isinstance(value, tuple):
            l, r = value
            if isinstance(l, float):
                var.continuous_variable.l = l
                var.continuous_variable.r = r
            else:
                var.integer_variable.l = l
                var.integer_variable.r = r
        else:
            var.categorical_variable.categories[:] = value
        var.direct_input.SetInParent()
        header.job.optimization_job.task_variables.append(var)
    start_time = time.time()
    task_id = stub.NewTask(request_generator(header, path)).task_id
    response = _wait_for_task(stub, task_id)
    completed_job = response.job
    finish_time = time.time()
    print('Total time: %f seconds' % (finish_time - start_time))
    print('Result: %f' % completed_job.optimization_job.result)
    print('Listing variables')
    for var in completed_job.optimization_job.variables:
        name = var.name
        if var.HasField('continuous_value'):
            value = var.continuous_value.value
        elif var.HasField('integer_value'):
            value = var.integer_value.value
        else:
            value = var.categorical_value.value
        print('%s = %s' % (name, str(value)))
    print('Example complete\n\n')


def main():
    args = parser.parse_args()
    channel = grpc.insecure_channel(args.server_address)
    stub = blackbox_server_pb2_grpc.BlackboxStub(channel)
    if args.algorithm == 'random_search':
        algorithm = job_pb2.Algorithm.RANDOM_SEARCH
    elif args.algorithm == 'nelder_mead':
        algorithm = job_pb2.Algorithm.NELDER_MEAD
    else:
        algorithm = job_pb2.Algorithm.OPENTUNER
    _run_example(
        stub,
        'examples/files/sin_1d.py',
        algorithm,
        {
            'x': (-7.0, 7.0),
        }
    )
    _run_example(
        stub,
        'examples/files/rosenbrock_2d.py',
        algorithm,
        {
            'x': (-5.0, 5.0),
            'y': (-5.0, 5.0),
        }
    )
    if algorithm != job_pb2.Algorithm.NELDER_MEAD and algorithm != job_pb2.Algorithm.OPENTUNER:
        _run_example(
            stub,
            'examples/files/rock_paper_scissors.py',
            algorithm,
            {
                'first': ['rock', 'paper', 'scissors'],
                'second': ['rock', 'paper', 'scissors'],
            }
        )


if __name__ == '__main__':
    main()
