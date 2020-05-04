load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "blackbox_client",
    srcs = ["blackbox_client.py"],
    deps = [
        "//proto:blackbox_server_py_pb2_grpc",
        "//proto:blackbox_server_py_pb2",
    ],
)
