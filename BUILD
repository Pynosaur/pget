genrule(
    name = "pget_bin",
    srcs = glob(["app/**/*.py", "doc/**/*.yaml"]) + [".program"],
    outs = ["pget"],
    cmd = """
        _VER=$$(grep '^version:' $(location .program) | cut -d' ' -f2)
        /opt/homebrew/bin/nuitka \
            --onefile \
            --include-data-dir=doc=doc \
            --onefile-tempdir-spec=/tmp/nuitka-pget-$$_VER \
            --no-progressbar \
            --assume-yes-for-downloads \
            --output-dir=$$(dirname $(location pget)) \
            --output-filename=pget \
            $(location app/main.py)
    """,
    local = 1,
    visibility = ["//visibility:public"],
)

