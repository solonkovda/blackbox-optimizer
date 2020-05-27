load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@my_deps//:requirements.bzl", "requirement")

py_library(
    name = "config",
    srcs = ["config.py"],
)

py_library(
    name = "storage",
    srcs = ["storage.py"],
    deps = [
        ":config",
        requirement("psycopg2-binary"),
    ],
)

py_library(
    name = "jobs_handler",
    srcs = ["jobs_handler.py"],
    deps = [
        "//proto:jobs_handler_py_pb2",
        "//proto:jobs_handler_py_pb2_grpc",
    ],
)

py_library(
    name = "garbage_collector",
    srcs = ["garbage_collector.py"],
    deps = [
        ":config",
    ]
)

py_binary(
    name = "blackbox_server",
    srcs = ["blackbox_server.py"],
    deps = [
        ":config",
        ":garbage_collector",
        ":storage",
        ":jobs_handler",
        "//proto:blackbox_server_py_pb2",
        "//proto:blackbox_server_py_pb2_grpc",
    ]
)
