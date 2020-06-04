import proto.blackbox_server_pb2 as blackbox_server_pb2
import proto.blackbox_server_pb2_grpc as blackbox_server_pb2_grpc
import proto.blackbox_variable_pb2 as blackbox_variable_pb2
import proto.job_pb2 as job_pb2

import argparse
import enum
import time
import tempfile
import os
import shutil
import subprocess
import grpc

_ALGORITHM_CHOICES = [
    'random_search',
    'nelder_mead',
    'opentuner'
]
_EXAMPLE_CHOICES = [
    'finding_discrete_point.py',
    'rock_paper_scissors.py',
    'rosenbrock_2d.py',
    'simple_4_variable_knapsack.py',
    'sin_1d.py',
    'sin_1d_argument.py',
    'sin_1d_environment.py',
    'docker-sin-3d',
    'docker-catboost',
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
parser.add_argument('--run-only',
                    help='Runs only the given example, instead of running all of them',
                    choices=_EXAMPLE_CHOICES)
parser.add_argument('--run-docker-examples',
                    help='Run docker examples. Requires docker to be installed',
                    action='store_true')


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
        while data:
            r = blackbox_server_pb2.NewTaskRequest()
            r.body.chunk = data
            data = f.read(1024*1024)
            yield r


def _run_example(stub, path, algorithm, job_parameters, variables, constraints,
                 evaluation_type=job_pb2.EvaluationType.BINARY):
    print('Running %s' % path)
    print('Variables: %s' % str(variables))
    header = blackbox_server_pb2.NewTaskRequest()
    header.job.optimization_job.algorithm = algorithm
    header.job.optimization_job.job_parameters.CopyFrom(job_parameters)
    header.job.optimization_job.evaluation_type = evaluation_type
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

    for (vars, constant_term) in constraints:
        job_constraint = job_pb2.OptimizationJob.JobConstraint()
        job_constraint.constant_term = constant_term
        for name, coefficient in vars:
            variable_constraint = job_pb2.OptimizationJob.JobConstraint.VariableConstraint()
            variable_constraint.name = name
            variable_constraint.coefficient = coefficient
            job_constraint.variable_constraints.append(variable_constraint)
        header.job.optimization_job.job_constraints.append(job_constraint)


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


def prepare_docker_image(image_name, output_path):
    print('Pulling %s. This can take a while' % image_name)
    subprocess.run(
        ['docker', 'pull', image_name],
        stdout=subprocess.DEVNULL
    )
    print('Creating docker image')
    container_id = subprocess.check_output(['docker', 'create', image_name], encoding='ascii').strip()
    print('Exporting container to file. This can take a while')
    subprocess.run(['docker', 'export', '-o', output_path, container_id])
    print('Export complete')


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
    if not args.run_only or args.run_only == 'sin_1d.py':
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
            },
            []
        )
    if not args.run_only or args.run_only == 'sin_1d_argument.py':
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
            },
            []
        )
    if not args.run_only or args.run_only == 'sin_1d_environment.py':
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
            },
            []
        )
    if not args.run_only or args.run_only == 'rosenbrock_2d.py':
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
            },
            []
        )
    if (not args.run_only or args.run_only == 'rock_paper_scissors.py') and algorithm != job_pb2.Algorithm.NELDER_MEAD and algorithm != job_pb2.Algorithm.OPENTUNER:
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
            },
            []
        )
    if (not args.run_only or args.run_only == 'finding_discrete_point.py') and algorithm != job_pb2.Algorithm.NELDER_MEAD:
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
            },
            []
        )
    if (not args.run_only or args.run_only == 'simple_4_variable_knapsack.py') and algorithm != job_pb2.Algorithm.NELDER_MEAD:
        _run_example(
            stub,
            'examples/files/simple_4_variable_knapsack.py',
            algorithm,
            job_parameters,
            {
                'x1': (
                    (0, 10),
                    (InputType.DIRECT,)
                ),
                'x2': (
                    (0, 10),
                    (InputType.DIRECT,)
                ),
                'x3': (
                    (0, 10),
                    (InputType.DIRECT,)
                ),
                'x4': (
                    (0, 10),
                    (InputType.DIRECT,)
                ),
            },
            [
                (
                    [
                        ('x1', 60),
                        ('x2', 1),
                        ('x3', 30),
                        ('x4', 35),
                    ],
                    99.5,
                )
            ],
        )
    if args.run_docker_examples:
        tmp = tempfile.mkdtemp()
        try:
            container_file_path = os.path.join(tmp, 'container.data')
            if not args.run_only or args.run_only == 'docker-sin-3d':
                prepare_docker_image(
                    'solonkovda/blackbox_optimizer_docker_example_sin_3d',
                    container_file_path
                )
                _run_example(
                    stub,
                    container_file_path,
                    algorithm,
                    job_parameters,
                    {
                        'x': (
                            (-7.0, 7.0),
                            (InputType.DIRECT,)
                        ),
                        'y': (
                            (-7.0, 7.0),
                            (InputType.ARGUMENT, 'y', True)
                        ),
                        'z': (
                            (-7.0, 7.0),
                            (InputType.ENV, 'z')
                        ),
                    },
                    [],
                    job_pb2.EvaluationType.DOCKER_EXPORT,
                )
            if not args.run_only or args.run_only == 'docker-catboost':
                prepare_docker_image(
                    'solonkovda/blackbox_optimizer_docker_example_catboost',
                    container_file_path
                )
                _run_example(
                    stub,
                    container_file_path,
                    algorithm,
                    job_parameters,
                    {
                        'iterations': (
                            (1, 20),
                            (InputType.DIRECT,)
                        ),
                        'learning_rate': (
                            (0.001, 1),
                            (InputType.DIRECT,)
                        ),
                        'l2_leaf_reg': (
                            (1.0, 10.0),
                            (InputType.DIRECT,)
                        ),
                        'bagging_temperature': (
                            (0.0, 10.0),
                            (InputType.DIRECT,)
                        ),
                        'subsample': (
                            (0.0, 1.0),
                            (InputType.DIRECT,)
                        ),
                        'random_strength': (
                            (0.0, 1.0),
                            (InputType.DIRECT,)
                        ),
                        'depth': (
                            (1, 16),
                            (InputType.DIRECT,)
                        ),
                        'min_data_in_leaf': (
                            (1, 10),
                            (InputType.DIRECT,)
                        ),
                        'rsm': (
                            (0.0, 1.0),
                            (InputType.DIRECT,)
                        ),
                    },
                    [],
                    job_pb2.EvaluationType.DOCKER_EXPORT,
                )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
