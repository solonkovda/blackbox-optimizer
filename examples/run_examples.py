import proto.blackbox_server_pb2 as blackbox_server_pb2
import proto.blackbox_server_pb2_grpc as blackbox_server_pb2_grpc
import proto.blackbox_variable_pb2 as blackbox_variable_pb2
import proto.job_pb2 as job_pb2

import argparse
import enum
import time
import grpc

_ALGORITHM_CHOICES = [
    'random_search',
    'nelder_mead',
    'opentuner'
]

class InputType(enum.Enum):
    DIRECT = 1
    ARGUMENT = 2
    ENV = 3

parser = argparse.ArgumentParser()
parser.add_argument('--server-address',
                    help='Address of the server',
                    default='localhost:50051')
parser.add_argument('--algorithm',
                    help='Algorithm to use',
                    default='random_search',
                    choices=_ALGORITHM_CHOICES)
parser.add_argument('--time-limit',
                    help='Time limit in seconds. 0 for unlimited',
                    type=float,
                    default=0)
parser.add_argument('--evaluation-limit',
                    help='Limit of permitted evaluations. 0 for unlimited',
                    type=int,
                    default=0)


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


def _run_example(stub, path, algorithm, job_parameters, variables):
    print('Running %s' % path)
    print('Variables: %s' % str(variables))
    header = blackbox_server_pb2.NewTaskRequest()
    header.job.optimization_job.algorithm = algorithm
    header.job.optimization_job.job_parameters.CopyFrom(job_parameters)
    for name, (value, input_type) in variables.items():
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
        if input_type[0] == InputType.DIRECT:
            var.direct_input.SetInParent()
        elif input_type[0] == InputType.ARGUMENT:
            var.argument_input.arg_name = input_type[1]
            var.argument_input.long_arg = input_type[2]
        else:
            var.environment_input.env_name = input_type[1]
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
    job_parameters = job_pb2.OptimizationJob.JobParameters()
    if args.time_limit > 0:
        job_parameters.time_limit = args.time_limit
    if args.evaluation_limit > 0:
        job_parameters.max_evaluations = args.evaluation_limit
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
        job_parameters,
        {
            'x': (
                (-7.0, 7.0),
                (InputType.DIRECT,)
            ),
        }
    )
    _run_example(
        stub,
        'examples/files/sin_1d_argument.py',
        algorithm,
        job_parameters,
        {
            'x': (
                (-7.0, 7.0),
                (InputType.ARGUMENT, 'x', True)
            ),
        }
    )
    _run_example(
        stub,
        'examples/files/sin_1d_environment.py',
        algorithm,
        job_parameters,
        {
            'x': (
                (-7.0, 7.0),
                (InputType.ENV, 'X')
            ),
        }
    )
    _run_example(
        stub,
        'examples/files/rosenbrock_2d.py',
        algorithm,
        job_parameters,
        {
            'x': (
                (-5.0, 5.0),
                (InputType.DIRECT,)
            ),
            'y': (
                (-5.0, 5.0),
                (InputType.DIRECT, )
            ),
        }
    )
    if algorithm != job_pb2.Algorithm.NELDER_MEAD and algorithm != job_pb2.Algorithm.OPENTUNER:
        _run_example(
            stub,
            'examples/files/rock_paper_scissors.py',
            algorithm,
            job_parameters,
            {
                'first': (
                    ['rock', 'paper', 'scissors'],
                    (InputType.DIRECT,)
                ),
                'second': (
                    ['rock', 'paper', 'scissors'],
                    (InputType.DIRECT,)
                ),
            }
        )
    if algorithm != job_pb2.Algorithm.NELDER_MEAD:
        _run_example(
            stub,
            'examples/files/finding_discrete_point.py',
            algorithm,
            job_parameters,
            {
                'x': (
                    (0, 100),
                    (InputType.DIRECT,)
                ),
                'y': (
                    (0, 100),
                    (InputType.DIRECT,)
                ),
            }
        )


if __name__ == '__main__':
    main()
