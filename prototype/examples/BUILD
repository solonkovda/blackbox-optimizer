load("@rules_python//python:defs.bzl", "py_binary")

filegroup(
    name = "examples",
    srcs = glob(["*"], exclude=["BUILD", "run_examples.py"]),
)

py_binary(
    name = "run_examples",
    srcs = ["run_examples.py"],
    data = [":examples"],
    deps = [
        "//proto:blackbox_server_py_pb2_grpc",
        "//proto:blackbox_server_py_pb2",
        "//proto:job_py_pb2",
    ]
)
