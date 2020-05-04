load("@rules_python//python:defs.bzl", "py_library")
package(default_visibility = ["//prototype/server:__subpackages__"])

py_library(
    name = "base",
    srcs = ["base.py"],
)

py_library(
    name = "random_search",
    srcs = ["random_search.py"],
    deps = [":base"],
)

py_library(
    name = "simulated_annealing",
    srcs = ["simulated_annealing.py"],
    deps = [":base"],
)
