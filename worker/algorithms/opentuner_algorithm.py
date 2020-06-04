import worker.algorithms.base as base
import worker.config as config

import argparse
import time
import math
import logging
import opentuner
from opentuner.api import TuningRunManager
from opentuner.measurement.interface import DefaultMeasurementInterface
from opentuner.resultsdb.models import Result
from opentuner.search.manipulator import ConfigurationManipulator
from opentuner.search.manipulator import FloatParameter, IntegerParameter, EnumParameter

_FAILED_JOBS_COEF = 100
_THRESHOLD_EPS = 1e-5


class OpentunerAlgorithm(base.AlgorithmBase):
    def solve(self, job):
        logging.debug('Starting opentuner')
        failed_jobs_threshold = self.jobs_limit * _FAILED_JOBS_COEF
        manipulator = ConfigurationManipulator()
        for var in job.optimization_job.task_variables:
            if var.HasField('continuous_variable'):
                cont_var = var.continuous_variable
                param = FloatParameter(var.name, cont_var.l, cont_var.r)
            else:
                int_var = var.integer_variable
                param = IntegerParameter(var.name, int_var.l, int_var.r)
            manipulator.add_parameter(param)
        parser = argparse.ArgumentParser(parents=opentuner.argparsers())
        args = parser.parse_args([])
        args.parallelism = 4
        args.no_dups = True
        interface = DefaultMeasurementInterface(args=args,
                                                manipulator=manipulator,
                                                project_name=job.job_id)
        api = TuningRunManager(interface, args)
        jobs = []
        current_value = None
        failed_jobs = 0
        while failed_jobs < failed_jobs_threshold and not self._check_for_termination(job):
            remaining_jobs = []
            for job_id, desired_result in jobs:
                res = self._get_evaluation_job_result(job_id)
                if res is not None:
                    if current_value is None or current_value > res + _THRESHOLD_EPS:
                        failed_jobs = 0
                    else:
                        failed_jobs += 1
                    result = Result(time=res)
                    api.report_result(desired_result, result)
                else:
                    remaining_jobs.append((job_id, desired_result))
            jobs = remaining_jobs
            while len(jobs) < self.jobs_limit:
                desired_result = api.get_next_desired_result()
                if desired_result is None:
                    break
                job_id = self._start_evaluation_job(job, desired_result.configuration.data)
                if job_id is None:
                    api.report_result(desired_result, Result(time=math.inf))
                else:
                    jobs.append((job_id, desired_result))
            if not jobs:
                break
            r = api.get_best_result()
            if r is not None:
                current_value = r.time
                logging.debug('Opentuner current state: %s %s', r.time, api.get_best_configuration())
            time.sleep(5)
        res = api.get_best_result().time
        vars = api.get_best_configuration()
        api.finish()
        return res, vars
