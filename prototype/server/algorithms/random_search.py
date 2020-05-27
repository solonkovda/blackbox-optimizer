import prototype.server.algorithms.base as base
import random

_RANDOM_SEARCH_MAX_FAILED_STEPS = 100
_RANDOM_SEARCH_RADIUS = 1


class RandomSearchBlackboxSolver(base.BlackboxSolver):
    def _random_search_step(self, variables):
        new_variables = []
        for i, variable in enumerate(self.optimization_job.task_variables):
            if variable.HasField('continuous_variable'):
                cont_var = variable.continuous_variable
                l = max(cont_var.l, variables[i] - _RANDOM_SEARCH_RADIUS)
                r = min(cont_var.r, variables[i] + _RANDOM_SEARCH_RADIUS)
                value = random.uniform(l, r)
            elif variable.HasField('integer_variable'):
                int_var = variable.integer_variable
                l = max(int_var.l, round(variables[i] - _RANDOM_SEARCH_RADIUS))
                r = min(int_var.r, round(variables[i] + _RANDOM_SEARCH_RADIUS))
                value = random.randint(l, r)
            else:
                cat_var = variable.categorical_variable
                value = random.choice(cat_var.categories)
            new_variables.append(value)
        return new_variables

    def solve(self):
        variables = self._generate_initial_values()
        current_value = self.evaluator.evaluate(self.optimization_job.task_variables, variables)
        failed_steps = 0
        while failed_steps < _RANDOM_SEARCH_MAX_FAILED_STEPS:
            new_variables = self._random_search_step(variables)
            new_value = self.evaluator.evaluate(self.optimization_job.task_variables, new_variables)
            if new_value > current_value:
                variables, current_value = new_variables, new_value
                failed_steps = 0
            else:
                failed_steps += 1
        return current_value, variables
