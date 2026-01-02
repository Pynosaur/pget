genrule(
    name = "pget_bin",
    srcs = glob(["app/**/*.py", "doc/**/*.yaml"]),
    outs = ["pget"],
    cmd = """
        /opt/homebrew/bin/nuitka \
            --onefile \
            --include-data-dir=doc=doc \
            --onefile-tempdir-spec=/tmp/nuitka-pget \
            --no-progressbar \
            --assume-yes-for-downloads \
            --output-dir=$$(dirname $(location pget)) \
            --output-filename=pget \
            $(location app/main.py)
    """,
    local = 1,
    visibility = ["//visibility:public"],
)

