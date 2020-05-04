load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_library(
    name = "blackbox_evaluator",
    srcs = ["blackbox_evaluator.py"],
)

py_library(
    name = "config",
    srcs = ["config.py"],
)

py_library(
    name = "storage",
    srcs = ["storage.py"],
    deps = [":config"],
)

py_binary(
    name = "blackbox_optimizer",
    srcs = [
        "blackbox_optimizer.py",
    ],
    deps = [
        "//prototype/server/algorithms:random_search",
        "//prototype/server/algorithms:simulated_annealing",
        "//prototype/server/proto:blackbox_server_py_pb2",
        ":blackbox_evaluator",
        ":storage",
        ":config",
    ],
)

py_binary(
    name = "blackbox_server",
    srcs = ["blackbox_server.py"],
    deps = [
        "//prototype/server/proto:blackbox_server_py_pb2_grpc",
        "//prototype/server/proto:blackbox_server_py_pb2",
        ":blackbox_optimizer"
    ],
)
