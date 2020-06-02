load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@my_deps//:requirements.bzl", "requirement")
package(default_visibility = ["//worker:__subpackages__"])

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
    name = "nelder_mead",
    srcs = ["nelder_mead.py"],
    deps = [":base"],
)

py_library(
    name = "opentuner_algorithm",
    srcs = ["opentuner_algorithm.py"],
    deps = [
        ":base",
        requirement("opentuner"),
    ],
)
