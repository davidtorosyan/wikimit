import subprocess
from pathlib import Path


def run(
    cmd: list[str],
    cwd: Path | None = None,
) -> None:
    try:
        subprocess.check_call(
            cmd,
            cwd=cwd,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(
            "failed to run command! Got error code %s for command: %s",
            e.returncode,
            " ".join(cmd),
        )


def run_check(
    cmd: list[str],
    cwd: Path | None = None,
) -> bool:
    try:
        subprocess.check_call(
            cmd,
            cwd=cwd,
        )
        return True
    except subprocess.CalledProcessError as _e:
        return False


def run_output(
    cmd: list[str],
    cwd: Path | None = None,
    error_okay: bool = False,
) -> str:
    try:
        output = subprocess.check_output(
            cmd,
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        )
        return _process_output(output)
    except subprocess.CalledProcessError as e:
        if error_okay:
            print(
                "error code, but not exiting due to error_okay. Got error code %s for command: %s",
                e.returncode,
                " ".join(cmd),
            )
            return _process_output(e.output)
        else:
            raise Exception(
                "failed to run command! Got error code %s for command: %s",
                e.returncode,
                " ".join(cmd),
            )


def _process_output(output: bytes) -> str:
    return output.decode("utf-8").strip()
