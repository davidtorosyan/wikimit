import logging
import signal
import subprocess
import threading
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

import typer
from output import configure, logger
from typing_extensions import Annotated

app = typer.Typer()
test_app = typer.Typer()
app.add_typer(test_app, name="test")


WIKIMIT_ENGINE_DIR = Path(__file__).parent.parent.parent / "src" / "wikimit-engine"

DOCKER_STEPFUNCTIONS_LOCAL_NAME = "integration-test-stepfunctions"


class CleanupWhen(str, Enum):
    always = "always"
    never = "never"
    on_success = "on_success"


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
    """Script runner for wikimit-engine"""
    if verbose == 1:
        configure(logging.INFO)
    elif verbose == 2:
        configure(logging.DEBUG)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def build():
    """Build the application"""
    run_sam_build()


@test_app.callback(invoke_without_command=True)
def test_main(ctx: typer.Context):
    """Run tests"""
    if ctx.invoked_subcommand is None:
        test_setup()
        run_unit_tests()
        run_integration_tests_with_docker(CleanupWhen.on_success)


@test_app.command("unit")
def test_unit():
    """Run unit tests"""
    test_setup()
    run_unit_tests()


@test_app.command("int")
def test_integration(
    cleanup_when: Annotated[
        CleanupWhen,
        typer.Option(
            "--cleanup-when",
            "-cw",
            case_sensitive=False,
            help="when to clean up the stepfunction",
        ),
    ] = CleanupWhen.on_success,
):
    """Run integration tests. Requires docker."""
    test_setup()
    run_integration_tests_with_docker(cleanup_when)


def test_setup():
    run_sam_build()
    install_test_requirements()


def run_integration_tests_with_docker(cleanup_when: CleanupWhen):
    with thread_sam_local_start_lambda():
        with docker_stepfunctions_local(DOCKER_STEPFUNCTIONS_LOCAL_NAME, cleanup_when):
            run_integration_tests()


@contextmanager
def docker_stepfunctions_local(name: str, cleanup_when: CleanupWhen):
    success = False
    try:
        start_docker_stepfunctions_local(name)
        yield
        success = True
    finally:
        if cleanup_when == CleanupWhen.always or (
            cleanup_when == CleanupWhen.on_success and success
        ):
            stop_docker_stepfunctions_local(name)
            remove_docker_stepfunctions_local(name)
        else:
            logger.warning("Skipping stepfunction cleanup")


def run_sam_build() -> None:
    logger.print("Building")
    _run_command_wikimit("sam build --use-container")


def install_test_requirements():
    logger.print("Setting up environment")
    _run_command_wikimit("pip install -r tests/requirements.txt --user")


def run_unit_tests():
    logger.print("Running unit tests")
    _run_command_wikimit("python -m pytest tests/unit -v")
    logger.success("Unit tests passed")


@contextmanager
def thread_sam_local_start_lambda():
    logger.print("Starting local lambda")
    with _thread_command_wikimit("sam local start-lambda"):
        logger.print("Waiting for local lambda to start")
        time.sleep(5)
        yield


def start_docker_stepfunctions_local(name: str) -> subprocess.Popen[str]:
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
    logger.success("Integration tests passed")


def _run_command_wikimit(command: str) -> str:
    return _run_command(command, working_dir=WIKIMIT_ENGINE_DIR)


def _start_command_wikimit(command: str) -> subprocess.Popen[str]:
    return _start_command(command, working_dir=WIKIMIT_ENGINE_DIR)


@contextmanager
def _thread_command_wikimit(command: str):
    with _thread_command(command, working_dir=WIKIMIT_ENGINE_DIR):
        yield


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
        logger.debug("> Success")
        logger.debug(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error("> Failure")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        raise typer.Exit(code=1)


def _start_command(
    command: str, working_dir: Path | None = None
) -> subprocess.Popen[str]:
    logger.info(f"% {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
            text=True,
        )
        logger.debug("> Started")
        return process
    except subprocess.CalledProcessError as e:
        logger.error("> Failure")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        raise typer.Exit(code=1)


def _run_command_threaded(
    command: str, working_dir: Path | None = None
) -> tuple[threading.Thread, subprocess.Popen[str]]:
    process = _start_command(command, working_dir)

    def run_command():
        try:
            logger.debug("Started thread")
            process.communicate()
            logger.debug("Finished thread")
        except Exception as e:
            logger.debug(f"Exception in thread: {e}")

    thread = threading.Thread(target=run_command)
    thread.start()
    return (thread, process)


@contextmanager
def _thread_command(command: str, working_dir: Path | None = None):
    thread, process = None, None
    try:
        thread, process = _run_command_threaded(command, working_dir)
        yield
    finally:
        if process:
            process.send_signal(signal.CTRL_C_EVENT)
            process.terminate()
        if thread:
            try:
                thread.join()
            except KeyboardInterrupt:
                logger.debug("Caught keyboard interrupt in thread join")


if __name__ == "__main__":
    app()
