import os
import subprocess
import sys


def is_39():
    return sys.version_info >= (3, 9)


def main(quiet):
    """
    Python 3.9 Notes
    ================
    Especially on macOS, there are still many missing wheels for Python 3.9, which means that some
    dependencies may have to be built from source. You may find yourself needing to install system
    packages such as freetype, gfortran, etc.; on macOS, Homebrew should suffice.

    Tensorflow is still not available for 3.9 (2020-12-10), so we have put conditional logic in place
    around examples, etc., that make use of it. https://github.com/tensorflow/tensorflow/issues/44485

    Pyarrow is still not available for 3.9 (2020-12-10). https://github.com/apache/arrow/pull/8386

    As a consequence of pyarrow, the snowflake connector also is not yet avaialble for 3.9 (2020-12-10).
    https://github.com/snowflakedb/snowflake-connector-python/issues/562
    """

    # Previously, we did a pip install --upgrade pip here. We have removed that and instead
    # depend on the user to ensure an up-to-date pip is installed and available. For context, there
    # is a lengthy discussion here: https://github.com/pypa/pip/issues/5599

    # On machines with less memory, pyspark install will fail... see:
    # https://stackoverflow.com/a/31526029/11295366
    cmd = ["pip", "--no-cache-dir", "install", "pyspark>=3.0.1"]
    if quiet:
        cmd.append(quiet)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(" ".join(cmd))  # pylint: disable=print-call
    while True:
        output = p.stdout.readline()
        if p.poll() is not None:
            break
        if output:
            print(output.decode("utf-8").strip())  # pylint: disable=print-call

    install_targets = []

    # Need to do this for 3.9 compat
    # This is to ensure we can build Pandas on 3.9
    # See: https://github.com/numpy/numpy/issues/17784,
    if is_39():
        install_targets += ["Cython==0.29.21", "numpy==1.18.5"]

    install_targets += [
        "awscli",
        "-e python_modules/dagster[test]",
        "-e python_modules/dagster-graphql",
        "-e python_modules/dagster-test",
        "-e python_modules/dagit",
        "-e python_modules/automation",
        "-e python_modules/libraries/dagster-pandas",
        "-e python_modules/libraries/dagster-aws[test]",
        "-e python_modules/libraries/dagster-celery",
        "-e python_modules/libraries/dagster-celery-docker",
        "-e python_modules/libraries/dagster-cron",
        '-e "python_modules/libraries/dagster-dask[yarn,pbs,kube]"',
        "-e python_modules/libraries/dagster-datadog",
        "-e python_modules/libraries/dagster-dbt",
        "-e python_modules/libraries/dagster-docker",
        "-e python_modules/libraries/dagster-gcp",
        "-e python_modules/libraries/dagster-k8s",
        "-e python_modules/libraries/dagster-celery-k8s",
        "-e python_modules/libraries/dagster-github",
        "-e python_modules/libraries/dagster-mysql",
        "-e python_modules/libraries/dagster-pagerduty",
        "-e python_modules/libraries/dagster-papertrail",
        "-e python_modules/libraries/dagster-postgres",
        "-e python_modules/libraries/dagster-prometheus",
        "-e python_modules/libraries/dagster-spark",
        "-e python_modules/libraries/dagster-pyspark",
        "-e python_modules/libraries/dagster-databricks",
        "-e python_modules/libraries/dagster-shell",
        "-e python_modules/libraries/dagster-slack",
        "-e python_modules/libraries/dagster-ssh",
        "-e python_modules/libraries/dagster-twilio",
        "-e python_modules/libraries/lakehouse",
        "-e python_modules/libraries/dagster-airflow",
        "-e integration_tests/python_modules/dagster-k8s-test-infra",
        "-r scala_modules/scripts/requirements.txt",
        "-e python_modules/libraries/dagster-azure",
        "-e helm/dagster/schema[test]",
    ]

    # dagster-ge depends on a great_expectations version that does not install on Windows
    # https://github.com/dagster-io/dagster/issues/3319
    if not os.name == "nt":
        install_targets += ["-e python_modules/libraries/dagster-ge"]

    if not is_39():
        install_targets += [
            "-e python_modules/libraries/dagster-snowflake",
            "-e python_modules/libraries/dagstermill",
            '-e "examples/airline_demo[full]"',
        ]

    # NOTE: These need to be installed as one long pip install command, otherwise pip will install
    # conflicting dependencies, which will break pip freeze snapshot creation during the integration
    # image build!

    # pip install twice. First, without dependencies.
    # When this completes, we'll have all of our editable projects installed but none of their
    # pypi dependencies.
    # If we try with dependencies on master, pip fails to find "dagster==dev" in pypi and
    # short-circuits installation. This worked prior to https://dagster.phacility.com/D7506
    # because the version always existed on pypi; dependency resolution was satisfied even
    # though we weren't actually installing the version.
    cmd = ["pip", "install", "--no-deps"] + install_targets
    if quiet:
        cmd.append(quiet)

    # Second, install with dependencies. Now, pip will see that the editable installs already
    # exist and will use them instead of trying to find the projects on pypi.
    cmd += ["&&", "pip", "install"] + install_targets
    if quiet:
        cmd.append(quiet)

    p = subprocess.Popen(
        " ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )
    print(" ".join(cmd))  # pylint: disable=print-call
    while True:
        output = p.stdout.readline()
        if p.poll() is not None:
            break
        if output:
            print(output.decode("utf-8").strip())  # pylint: disable=print-call


if __name__ == "__main__":
    main(quiet=sys.argv[1] if len(sys.argv) > 1 else "")
