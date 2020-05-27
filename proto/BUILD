load("@rules_proto//proto:defs.bzl", "proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library")
load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")
package(default_visibility = ["//visibility:public"])

proto_library(
    name = "blackbox_variable_proto",
    srcs = [
        "blackbox_variable.proto",
    ],
)

py_proto_library(
    name = "blackbox_variable_py_pb2",
    srcs = ["blackbox_variable.proto"],
)

proto_library(
    name = "job_proto",
    srcs = [
        "job.proto",
    ],
    deps = [":blackbox_variable_proto"]
)

py_proto_library(
    name = "job_py_pb2",
    srcs = ["job.proto"],
    deps = [":blackbox_variable_py_pb2"]
)

proto_library(
    name = "blackbox_server_proto",
    srcs = [
        "blackbox_server.proto",
    ],
    deps = [":job_proto"]
)

py_proto_library(
    name = "blackbox_server_py_pb2",
    srcs = ["blackbox_server.proto"],
    deps = [":job_py_pb2"]
)

py_grpc_library(
    name = "blackbox_server_py_pb2_grpc",
    srcs = [":blackbox_server_proto"],
    deps = [
        ":blackbox_server_py_pb2",
    ],
)

proto_library(
    name = "jobs_handler_proto",
    srcs = [
        "jobs_handler.proto",
    ],
    deps = [
        ":job_proto",
    ],
)

py_proto_library(
    name = "jobs_handler_py_pb2",
    srcs = ["jobs_handler.proto"],
    deps = [
        ":job_py_pb2",
    ],
)

py_grpc_library(
    name = "jobs_handler_py_pb2_grpc",
    srcs = [":jobs_handler_proto"],
    deps = [
        ":jobs_handler_py_pb2",
    ]
)
