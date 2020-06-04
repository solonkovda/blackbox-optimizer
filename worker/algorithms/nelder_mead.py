import worker.algorithms.base as base

import logging
import random

_ITERATION_DIFF_THREASHOLD = 1e-4


def _calc_centroid(arr):
    res = dict()
    for vars in arr:
        for key, value in vars.items():
            if key not in res:
                res[key] = 0
            res[key] += value
    for key in res:
        res[key] /= len(arr)
    return res


def _calc_reflection(centroid, last_point):
    result = dict()
    for key in centroid:
        result[key] = centroid[key] + (centroid[key] - last_point[key])
    return result


def _calc_expansion(centroid, reflection_point):
    result = dict()
    for key in centroid:
        result[key] = centroid[key] + 2 * (reflection_point[key] - centroid[key])
    return result


def _calc_contraction(centroid, last_point):
    result = dict()
    for key in centroid:
        result[key] = centroid[key] + (1/2) * (last_point[key] - centroid[key])
    return result


def _calc_shrink(point, best_point):
    result = dict()
    for key in point:
        result[key] = best_point[key] + (1/2) * (point[key] - best_point[key])
    return result


class NelderMead(base.AlgorithmBase):
    def _generate_initial_vertices(self, job):
        jobs = []
        for _ in range(len(job.optimization_job.task_variables) + 1):
            vars = dict()
            for var in job.optimization_job.task_variables:
                cont_var = var.continuous_variable
                vars[var.name] = random.uniform(cont_var.l, cont_var.r)
            job_id = self._start_evaluation_job(job, vars)
            jobs.append((job_id, vars))

        return self._wait_for_job_list(jobs)

    def solve(self, job):
        current_vertices = self._generate_initial_vertices(job)
        current_best = current_vertices[0]

        previous_iteration_values = None
        while not self._check_for_termination(job):
            current_vertices.sort(key=lambda x: x[0])
            if current_vertices[0][0] < current_best[0]:
                current_best = current_vertices[0]
            logging.debug('Starting new stage, current best: %s', current_best)
            logging.debug('Current vertices: %s', current_vertices)
            vertices_value = list(map(lambda x: x[0], current_vertices))
            stripped_vertices = list(map(lambda x: x[1], current_vertices))

            if previous_iteration_values is not None:
                diff = 0
                for i in range(len(previous_iteration_values)):
                    diff += (previous_iteration_values[i] - vertices_value[i])**2
                diff /= len(previous_iteration_values)
                if diff < _ITERATION_DIFF_THREASHOLD:
                    break
            previous_iteration_values = vertices_value

            centroid = _calc_centroid(stripped_vertices[:-1])
            reflection_point = _calc_reflection(centroid, stripped_vertices[-1])
            expanded_point = _calc_expansion(centroid, reflection_point)
            contraction_point = _calc_contraction(centroid, stripped_vertices[-1])

            reflection_job_id = self._start_evaluation_job(job, reflection_point)
            expanded_job_id = self._start_evaluation_job(job, expanded_point)
            contraction_job_id = self._start_evaluation_job(job, contraction_point)

            reflection, expanded, contraction = self._wait_for_job_list([
                (reflection_job_id, reflection_point),
                (expanded_job_id, expanded_point),
                (contraction_job_id, contraction_point),
            ])
            if reflection[0] < vertices_value[0]:
                if expanded[0] < reflection[0]:
                    logging.debug('Replacing best by expanded')
                    current_vertices[-1] = expanded
                else:
                    logging.debug('Replacing best by reflection')
                    current_vertices[-1] = reflection
            elif reflection[0] < vertices_value[-1]:
                logging.debug('Replacing worst by reflection')
                current_vertices[-1] = reflection
            elif contraction[0] < vertices_value[-1]:
                logging.debug('Replacing worst by contraction')
                current_vertices[-1] = contraction
            else:
                logging.debug('Shrinking everything')
                job_list = []
                for var in stripped_vertices[1:]:
                    new_var = _calc_shrink(var, stripped_vertices[0])
                    job_id = self._start_evaluation_job(job, new_var)
                    job_list.append((job_id, new_var))
                current_vertices[1:] = self._wait_for_job_list(job_list)
        return current_vertices[0]
