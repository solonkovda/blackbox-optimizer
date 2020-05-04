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
        "//prototype/server/proto:blackbox_server_py_pb2_grpc",
        "//prototype/server/proto:blackbox_server_py_pb2",
    ]
)
