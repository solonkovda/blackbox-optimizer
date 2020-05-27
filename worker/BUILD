load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_library(
    name = "config",
    srcs = ["config.py"],
    visibility = ['//worker:__subpackages__'],
)

py_binary(
    name = "evaluator_process",
    srcs = ["evaluator_process.py"],
    deps = [
        ":config",
        "//proto:jobs_handler_py_pb2",
        "//proto:jobs_handler_py_pb2_grpc",
    ],
)

py_binary(
    name = "optimization_process",
    srcs = ['optimization_process.py'],
    deps = [
        ':config',
        '//proto:blackbox_variable_py_pb2',
        '//proto:job_py_pb2',
        '//proto:jobs_handler_py_pb2',
        '//proto:jobs_handler_py_pb2_grpc',
        '//worker/algorithms:random_search',
        '//worker/algorithms:nelder_mead',
        '//worker/algorithms:opentuner_algorithm'
    ],
)

py_binary(
    name = "worker_client",
    srcs = [
        "worker_client.py",
        "evaluator_process.py",
    ],
    data = [
        ":evaluator_process",
        ":optimization_process",
    ],
    deps = [
        ":config",
        "//proto:jobs_handler_py_pb2",
        "//proto:jobs_handler_py_pb2_grpc",
    ],
)
