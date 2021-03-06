import worker.algorithms.base as base
import worker.config as config

import logging
import random
import math
import time

_START_DELTA = 1000
_MINIMAL_DELTA = 0.001
_ALLOWED_FAILS_COEFF = 2
_EPS_FOR_RESULT_VALUE = 0.001
_DELTA_REDUCTION_COEFF = 0.1


def _get_initial_delta(variables_metadata):
    current_delta = _MINIMAL_DELTA * 2
    for var in variables_metadata:
        if var.HasField('continuous_variable'):
            cont_var = var.continuous_variable
            current_delta = max(current_delta, cont_var.r - cont_var.l)
        elif var.HasField('integer_variable'):
            int_var = var.integer_variable
            current_delta = max(current_delta, int_var.r - int_var.l)
    return current_delta


def _generate_random_values(variables_metadata):
    variables = dict()
    for var in variables_metadata:
        if var.HasField('continuous_variable'):
            cont_var = var.continuous_variable
            value = random.uniform(cont_var.l, cont_var.r)
        elif var.HasField('integer_variable'):
            int_var = var.integer_variable
            value = random.randint(int_var.l, int_var.r)
        else:
            cat_var = var.categorical_variable
            value = random.choice(cat_var.categories)
        variables[var.name] = value
    return variables


def _random_search_step(variables, step_size, variables_metadata):
    new_variables = dict()
    for var in variables_metadata:
        current_value = variables[var.name]
        if var.HasField('continuous_variable'):
            cont_var = var.continuous_variable
            l = max(cont_var.l, current_value - step_size)
            r = min(cont_var.r, current_value + step_size)
            new_value = random.uniform(l, r)
        elif var.HasField('integer_variable'):
            int_var = var.integer_variable
            int_step_size = max(1, int(step_size))
            l = max(int_var.l, current_value - int_step_size)
            r = min(int_var.r, current_value + int_step_size)
            new_value = random.randint(l, r)
        else:
            cat_var = var.categorical_variable
            new_value = random.choice(cat_var.categories)
        new_variables[var.name] = new_value
    return new_variables


class RandomSearch(base.AlgorithmBase):
    def _generate_initial_values(self, job, variables_metadata):
        jobs = []
        for _ in range(self.jobs_limit):
            variables = _generate_random_values(variables_metadata)
            job_id = self._start_evaluation_job(job, variables)
            jobs.append((job_id, variables))
        done_jobs = []
        while len(jobs) > 0:
            completed_jobs, jobs = self._parse_job_list(jobs)
            done_jobs.extend(completed_jobs)
            if len(jobs) > 0:
                time.sleep(10)
        best_job = done_jobs[0]
        for (result, variables) in done_jobs:
            if result < best_job[0]:
                best_job = (result, variables)
        return best_job

    def solve(self, job):
        allowed_fails = self.jobs_limit * _ALLOWED_FAILS_COEFF
        cur_value, cur_variables = self._generate_initial_values(job, job.optimization_job.task_variables)
        while cur_value == math.inf:
            cur_value, cur_variables = self._generate_initial_values(job, job.optimization_job.task_variables)
        total_fails = 0
        jobs = []
        current_delta = _get_initial_delta(job.optimization_job.task_variables)
        while current_delta > _MINIMAL_DELTA and not self._check_for_termination(job):
            completed_jobs, jobs = self._parse_job_list(jobs)
            for result, variables in completed_jobs:
                if result < cur_value - _EPS_FOR_RESULT_VALUE:
                    cur_value, cur_variables = result, variables
                    total_fails = 0
                else:
                    total_fails += 1
            if total_fails > allowed_fails:
                total_fails = 0
                current_delta *= _DELTA_REDUCTION_COEFF
            while len(jobs) < self.jobs_limit:
                variables = _random_search_step(cur_variables, current_delta, job.optimization_job.task_variables)
                job_id = self._start_evaluation_job(job, variables)
                jobs.append((job_id, variables))
            time.sleep(5)
            logging.debug('Random search current state: %s %s', cur_value, str(cur_variables))
        return cur_value, cur_variables
