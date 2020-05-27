import prototype.server.algorithms.random_search as random_search
import prototype.server.algorithms.simulated_annealing as simulated_annealing
import proto.job_pb2 as pb2
import proto.blackbox_variable_pb2 as variable_pb2
import prototype.server.blackbox_evaluator as blackbox_evaluator
import prototype.server.storage as storage
import sys


def solve_blackbox(task_id, optimization_job, binary_path):
    evaluator = blackbox_evaluator.BlackboxBinaryFileEvaluator(binary_path)

    if optimization_job.algorithm == pb2.Algorithm.RANDOM_SEARCH:
        solver = random_search.RandomSearchBlackboxSolver(evaluator, optimization_job)
    else:
        solver = simulated_annealing.SimulatedAnnealingBlackboxSolver(evaluator, optimization_job)
    result, variables = solver.solve()

    completed_job = pb2.CompletedJob()
    completed_job.task_id = task_id
    completed_job.job_id = task_id
    completed_job.optimization_job.result = result

    for i, var_metadata in enumerate(optimization_job.task_variables):
        var_result = variable_pb2.BlackboxVariable()
        var_result.name = var_metadata.name
        value = variables[i]
        if var_metadata.HasField('continuous_variable'):
            var_result.continuous_value.value = value
        elif var_metadata.HasField('integer_variable'):
            var_result.integer_value.value = value
        else:
            var_result.categorical_value.value = value
        completed_job.optimization_job.variables.append(var_result)

    stor = storage.TaskStorageSqlite()
    stor.set_task_result(task_id, completed_job)


if __name__ == '__main__':
    task_id = sys.argv[1]
    binary_path = sys.argv[2]
    data = sys.stdin.buffer.read()
    optimization_job = pb2.OptimizationJob()
    optimization_job.ParseFromString(data)
    solve_blackbox(task_id, optimization_job, binary_path)
