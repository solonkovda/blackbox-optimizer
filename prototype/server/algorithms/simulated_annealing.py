import prototype.server.algorithms.base as base
import random
import math

_START_TEMP = 10
_MAX_FAILED_STEPS = 100
_CONTINUOUS_RANGE = 10


def _make_annealing_step(e, new_e, temp):
    if new_e > e:
        prob = 1
    else:
        prob = math.exp(-(e - new_e) / temp)
    return random.uniform(0, 1) < prob


class SimulatedAnnealingBlackboxSolver(base.BlackboxSolver):
    def _get_random_neighbour(self, variables):
        new_variables = []
        for i, variable in enumerate(self.optimization_job.task_variables):
            if variable.HasField('continuous_variable'):
                cont_var = variable.continuous_variable
                l = max(cont_var.l, variables[i] - _CONTINUOUS_RANGE)
                r = min(cont_var.r, variables[i] + _CONTINUOUS_RANGE)
                value = random.uniform(l, r)
            elif variable.HasField('integer_variable'):
                int_var = variable.integer_variable
                value = variables[i] + random.randint(-1, 1)
                value = max(int_var.l, value)
                value = min(int_var.r, value)
            else:
                cat_var = variable.categorical_variable
                value = random.choice(cat_var.categories)
            new_variables.append(value)
        return new_variables

    def solve(self):
        variables = self._generate_initial_values()
        current_value = self.evaluator.evaluate(self.optimization_job.task_variables, variables)
        failed_steps = 0
        steps_amount = 1
        while failed_steps < _MAX_FAILED_STEPS:
            new_variables = self._get_random_neighbour(variables)
            new_value = self.evaluator.evaluate(self.optimization_job.task_variables, new_variables)
            if _make_annealing_step(current_value, new_value, _START_TEMP / steps_amount**2):
                if new_value > current_value:
                    failed_steps = 0
                variables, current_value = new_variables, new_value
            else:
                failed_steps += 1
            steps_amount += 1
        return current_value, variables
