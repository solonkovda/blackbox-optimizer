load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "blackbox_client",
    srcs = ["blackbox_client.py"],
    deps = [
        "//prototype/server/proto:blackbox_server_py_pb2_grpc",
        "//prototype/server/proto:blackbox_server_py_pb2",
    ],
)
