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
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        test_unit()
        test_integration()


@test_app.command("unit")
def test_unit():
    logger.print("Running unit tests")


@test_app.command("int")
def test_integration():
    logger.print("Running integration tests")


def run_sam_build() -> None:
    _run_command("sam build --use-container", working_dir=WIKIMIT_ENGINE_DIR)


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


if __name__ == "__main__":
    app()
