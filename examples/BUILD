load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "run_examples",
    srcs = [
        "run_examples.py",
    ],
    data = ['//examples/files'],
    deps = [
        '//proto:blackbox_variable_py_pb2',
        '//proto:blackbox_server_py_pb2',
        '//proto:blackbox_server_py_pb2_grpc',
        '//proto:job_py_pb2',
    ]
)
