import logging
import subprocess
from contextlib import contextmanager
from pathlib import Path

import typer
from output import configure, logger

app = typer.Typer()
test_app = typer.Typer()
app.add_typer(test_app, name="test")


WIKIMIT_ENGINE_DIR = Path(__file__).parent.parent.parent / "src" / "wikimit-engine"

DOCKER_STEPFUNCTIONS_LOCAL_NAME = "integration-test-stepfunctions"


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="show more logs (or use -vv for even more)",
    ),
):
    if verbose == 1:
        configure(logging.INFO)
    elif verbose == 2:
        configure(logging.DEBUG)
    if ctx.invoked_subcommand is None:
        logger.print("hi")


@app.command()
def build():
    run_sam_build()


@test_app.callback(invoke_without_command=True)
def test_main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        test_unit()
        test_integration()


@test_app.command("unit")
def test_unit():
    install_test_requirements()
    run_unit_tests()


@test_app.command("int")
def test_integration():
    install_test_requirements()
    with docker_stepfunctions_local(DOCKER_STEPFUNCTIONS_LOCAL_NAME):
        run_integration_tests()


@contextmanager
def docker_stepfunctions_local(name: str):
    try:
        start_docker_stepfunctions_local(name)
        yield
    finally:
        stop_docker_stepfunctions_local(name)
        remove_docker_stepfunctions_local(name)


def run_sam_build() -> None:
    logger.print("Building")
    _run_command_wikimit("sam build --use-container")


def install_test_requirements():
    logger.print("Setting up environment")
    _run_command_wikimit("pip install -r tests/requirements.txt --user")


def run_unit_tests():
    logger.print("Running unit tests")
    _run_command_wikimit("python -m pytest tests/unit -v")


def start_sam_local_start_lambda() -> subprocess.Popen[bytes]:
    return _start_command_wikimit("sam local start-lambda")


def start_docker_stepfunctions_local(name: str) -> subprocess.Popen[bytes]:
    logger.print("Initializing local stepfunctions")
    return _start_command_wikimit(
        f'docker run -p "8083:8083" --name "{name}" --env-file tests/config/aws-stepfunctions-local-credentials.txt amazon/aws-stepfunctions-local'
    )


def stop_docker_stepfunctions_local(name: str):
    logger.print("Stopping local stepfunctions")
    return _run_command_wikimit(f'docker stop "{name}"')


def remove_docker_stepfunctions_local(name: str):
    logger.print("Removing local stepfunctions")
    return _run_command_wikimit(f'docker rm "{name}"')


def run_integration_tests():
    logger.print("Running integration tests")
    _run_command_wikimit("python -m pytest tests/integration -v")


def _run_command_wikimit(command: str) -> str:
    return _run_command(command, working_dir=WIKIMIT_ENGINE_DIR)


def _start_command_wikimit(command: str) -> subprocess.Popen[bytes]:
    return _start_command(command, working_dir=WIKIMIT_ENGINE_DIR)


def _run_command(command: str, working_dir: Path | None = None) -> str:
    logger.info(f"% {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
        )
        logger.success("> Success")
        logger.debug(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error("> Failure")
        logger.error(e.stderr)
        raise typer.Exit(code=1)


def _start_command(
    command: str, working_dir: Path | None = None
) -> subprocess.Popen[bytes]:
    logger.info(f"% {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
        )
        logger.success("> Started")
        return process
    except subprocess.CalledProcessError as e:
        logger.error("> Failure")
        logger.error(e.stderr)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
