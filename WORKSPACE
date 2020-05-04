load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",
    commit = "a0fbf98d4e3a232144df4d0d80b577c7a693b570",
)

load("@rules_python//python:repositories.bzl", "py_repositories")
py_repositories()
load("@rules_python//python:pip.bzl", "pip_repositories",)
pip_repositories()
load("@rules_python//python:pip.bzl", "pip3_import")

pip3_import(
   name = "my_deps",
   requirements = "//:requirements.txt"
)


load("@my_deps//:requirements.bzl", "pip_install")
pip_install()

http_archive(
    name = "com_github_grpc_grpc",
    sha256 = "3eb0b15a107aae2f61f49574e7131b2da368231e53d7acca59c25469a58c5ebe",
    strip_prefix = "grpc-a04f0db4dba6294035ba0d48270621d6357fba17",
    urls = [
        "https://github.com/grpc/grpc/archive/a04f0db4dba6294035ba0d48270621d6357fba17.tar.gz",
    ],
)

load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")
grpc_deps()

# TODO(https://github.com/grpc/grpc/issues/19835): Remove.
load("@upb//bazel:workspace_deps.bzl", "upb_deps")
upb_deps()

load("@build_bazel_rules_apple//apple:repositories.bzl", "apple_rules_dependencies")
apple_rules_dependencies()

load("@build_bazel_apple_support//lib:repositories.bzl", "apple_support_dependencies")
apple_support_dependencies()


http_archive(
    name = "rules_proto",
    sha256 = "602e7161d9195e50246177e7c55b2f39950a9cf7366f74ed5f22fd45750cd208",
    strip_prefix = "rules_proto-97d8af4dc474595af3900dd85cb3a29ad28cc313",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_proto/archive/97d8af4dc474595af3900dd85cb3a29ad28cc313.tar.gz",
        "https://github.com/bazelbuild/rules_proto/archive/97d8af4dc474595af3900dd85cb3a29ad28cc313.tar.gz",
    ],
)
load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")
rules_proto_dependencies()
rules_proto_toolchains()