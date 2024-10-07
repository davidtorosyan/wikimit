import logging
import subprocess
from pathlib import Path

import typer
from output import configure, logger

app = typer.Typer()
test_app = typer.Typer()
app.add_typer(test_app, name="test")


WIKIMIT_ENGINE_DIR = Path(__file__).parent.parent.parent / "src" / "wikimit-engine"


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
    logger.print("Building")
    run_sam_build()


@test_app.callback(invoke_without_command=True)
def test_main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        test_unit()
        test_integration()


@test_app.command("unit")
def test_unit():
    logger.print("Setting up environment")
    install_test_requirements()
    logger.print("Running unit tests")
    run_unit_tests()


@test_app.command("int")
def test_integration():
    logger.print("Setting up environment")
    install_test_requirements()
    logger.print("Initializing local lambda")
    run_sam_local_start_lambda()
    logger.print("Initializing local stepfunctions")
    run_docker_stepfunctions_local()
    logger.print("Running integration tests")
    run_integration_tests()


def run_sam_build() -> None:
    _run_command_wikimit("sam build --use-container")


def install_test_requirements():
    _run_command_wikimit("pip install -r tests/requirements.txt --user")


def run_unit_tests():
    _run_command_wikimit("python -m pytest tests/unit -v")


def run_sam_local_start_lambda():
    _start_command_wikimit("sam local start-lambda")


def run_docker_stepfunctions_local():
    _start_command_wikimit(
        'docker run -p "8083:8083" --env-file tests/config/aws-stepfunctions-local-credentials.txt amazon/aws-stepfunctions-local'
    )


def run_integration_tests():
    _run_command_wikimit("python -m pytest tests/integration -v")


def _run_command_wikimit(command: str) -> None:
    _run_command(command, working_dir=WIKIMIT_ENGINE_DIR)


def _start_command_wikimit(command: str) -> subprocess.Popen[bytes]:
    return _start_command(command, working_dir=WIKIMIT_ENGINE_DIR)


def _run_command(command: str, working_dir: Path | None = None) -> None:
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
    except subprocess.CalledProcessError as e:
        logger.error("> Failure")
        logger.error(e.stderr)


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
        raise


if __name__ == "__main__":
    app()
