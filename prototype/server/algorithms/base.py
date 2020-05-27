import random

class BlackboxSolver(object):
    def __init__(self, evaluator, optimization_job):
        self.evaluator = evaluator
        self.optimization_job = optimization_job

    def _generate_initial_values(self):
        variables = []
        for variable in self.optimization_job.task_variables:
            if variable.HasField('continuous_variable'):
                cont_var = variable.continuous_variable
                value = random.uniform(cont_var.l, cont_var.r)
            elif variable.HasField('integer_variable'):
                int_var = variable.integer_variable
                value = random.randint(int_var.l, int_var.r)
            else:
                cat_var = variable.categorical_variable
                value = random.choice(cat_var.categories)
            variables.append(value)
        return variables

    def solve(self):
        raise NotImplementedError()
