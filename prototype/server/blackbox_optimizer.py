import prototype.server.algorithms.random_search as random_search
import prototype.server.algorithms.simulated_annealing as simulated_annealing
import proto.blackbox_server_pb2 as pb2
import prototype.server.blackbox_evaluator as blackbox_evaluator
import prototype.server.storage as storage
import sys


def solve_blackbox(task_id, metadata, binary_path):
    evaluator = blackbox_evaluator.BlackboxBinaryFileEvaluator(binary_path)

    if metadata.algorithm == pb2.NewTaskRequest.Algorithm.RANDOM_SEARCH:
        solver = random_search.RandomSearchBlackboxSolver(evaluator, metadata)
    else:
        solver = simulated_annealing.SimulatedAnnealingBlackboxSolver(evaluator, metadata)
    result, variables = solver.solve()

    response = pb2.GetTaskResultResponse()
    response.result = result
    for i, variable in enumerate(metadata.task_variables):
        variable_value = pb2.GetTaskResultResponse.VariableValue()
        variable_value.name = variable.name
        if variable.HasField('continious_variable'):
            variable_value.continious_value.value = variables[i]
        elif variable.HasField('integer_variable'):
            variable_value.integer_value.value = variables[i]
        else:
            variable_value.categorical_value.value = variables[i]
        response.variable_values.append(variable_value)

    stor = storage.TaskStorageSqlite()
    stor.set_task_result(task_id, response)


if __name__ == '__main__':
    task_id = sys.argv[1]
    binary_path = sys.argv[2]
    data = sys.stdin.buffer.read()
    metadata = pb2.NewTaskRequest.Metadata()
    metadata.ParseFromString(data)
    solve_blackbox(task_id, metadata, binary_path)
