import proto.job_pb2 as job_pb2
import proto.jobs_handler_pb2 as pb2
import proto.jobs_handler_pb2_grpc as pb2_grpc
import worker.config as config

import grpc
import subprocess
import shlex
import sys

_DOCKER_INIT_RUNFILE = '/entrypoint'


def run_binary(variables_value, variables_metadata, task_binary_path):
    args = [task_binary_path]
    env = {}
    direct_input = ''
    for var in job.evaluation_job.variables_metadata:
        if var.HasField('argument_input'):
            arg_name = '-'
            if var.argument_input.long_arg:
                arg_name += '-'
            arg_name += var.argument_input.arg_name
            args.append(shlex.quote(arg_name))
            args.append(shlex.quote(str(variables_value[var.name])))
        if var.HasField('environment_input'):
            env_name = var.environment_input.env_name
            env[env_name] = str(variables_value[var.name])
        if var.HasField('direct_input'):
            direct_input += str(variables_value[var.name]) + '\n'
    p = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        close_fds=True,
        env=env,
        encoding='ascii',
    )
    stdout, stderr = p.communicate(direct_input)
    return stdout.strip()


def run_docker(job_id, variables_value, variables_metadata, task_docker_path):
    return_code = subprocess.run(
        ['docker', 'inspect', job_id],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode
    if return_code:
        subprocess.check_output(['docker', 'import', task_docker_path, job_id])
    args = ['docker', 'run', '-i', '--rm']
    direct_input = ''
    for var in job.evaluation_job.variables_metadata:
        if var.HasField('environment_input'):
            env_name = var.environment_input.env_name
            args.append('-e')
            arg = '%s=%s' % (env_name, str(variables_value[var.name]))
            args.append(shlex.quote(arg))
        elif var.HasField('direct_input'):
            direct_input += str(variables_value[var.name]) + '\n'

    args.extend([job_id, _DOCKER_INIT_RUNFILE])
    for var in job.evaluation_job.variables_metadata:
        if var.HasField('argument_input'):
            arg_name = '-'
            if var.argument_input.long_arg:
                arg_name += '-'
            arg_name += var.argument_input.arg_name
            args.append(shlex.quote(arg_name))
            args.append(shlex.quote(str(variables_value[var.name])))
    p = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding='ascii',
    )
    stdout, stderr = p.communicate(direct_input)
    return stdout.strip()


def run_worker(job, client_id, task_file_path):
    variables_value = dict()
    for var in job.evaluation_job.variables:
        if var.HasField('continuous_value'):
            variables_value[var.name] = var.continuous_value.value
        elif var.HasField('integer_value'):
            variables_value[var.name] = var.integer_value.value
        else:
            variables_value[var.name] = var.categorical_value.value
    if job.evaluation_job.evaluation_type == job_pb2.EvaluationType.BINARY:
        stdout = run_binary(variables_value, job.evaluation_job.variables_metadata, task_file_path)
    else:
        stdout = run_docker(job.evaluation_job.evaluation_job_id, variables_value, job.evaluation_job.variables_metadata, task_file_path)

    request = pb2.CompleteJobRequest()
    request.client_id = client_id
    request.completed_job.job_id = job.job_id
    request.completed_job.task_id = job.evaluation_job.evaluation_job_id
    request.completed_job.evaluation_job.result = float(stdout.strip())
    channel = grpc.insecure_channel(config.SERVER_ADDRESS)
    stub = pb2_grpc.JobsHandlerStub(channel)
    stub.CompleteJob(request)


if __name__ == '__main__':
    data = sys.stdin.buffer.read()
    job = job_pb2.Job()
    job.ParseFromString(data)
    run_worker(job, sys.argv[1], sys.argv[2])
