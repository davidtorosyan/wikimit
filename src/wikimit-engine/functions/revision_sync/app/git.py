from dataclasses import dataclass
from pathlib import Path

from .run import run, run_check, run_output


@dataclass
class Commit:
    message: str
    author: str
    description: str
    date: str


def repo_root(cwd: Path) -> str:
    return run_output(["git", "rev-parse", "--show-toplevel"], error_okay=True, cwd=cwd)


def status(cwd: Path) -> str:
    return run_output(["git", "status", "--porcelain"], cwd=cwd)


def has_commits(cwd: Path) -> bool:
    return run_check(["git", "show"], cwd=cwd)


def init(cwd: Path) -> None:
    run(["git", "init", "--initial-branch", "main"], cwd=cwd)


def add(cwd: Path, name: str) -> None:
    run(["git", "add", name], cwd=cwd)


def commit_initial(cwd: Path) -> None:
    run(["git", "commit", "-m", "Initial commit"], cwd=cwd)


def git_commit(cwd: Path, commit: Commit) -> None:
    run(
        [
            "git",
            "commit",
            "-m",
            commit.message,
            "-m",
            commit.description,
            "--date",
            commit.date,
            "--author",
            commit.author,
        ],
        cwd=cwd,
    )
