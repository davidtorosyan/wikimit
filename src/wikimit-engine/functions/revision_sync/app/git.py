from dataclasses import dataclass
from pathlib import Path

from dulwich import porcelain
from dulwich.errors import NotGitRepository
from dulwich.repo import Repo


@dataclass
class CommitInfo:
    message: str
    author: str
    description: str
    date: int


def repo_root(cwd: Path) -> str:
    try:
        return Repo(str(cwd)).path
    except NotGitRepository:
        return ""


def is_clean(cwd: Path) -> bool:
    (staged, unstaged, untracked) = porcelain.status(str(cwd))  # type: ignore
    return (
        len(staged["add"]) == 0  # type: ignore
        and len(staged["delete"]) == 0  # type: ignore
        and len(staged["modify"]) == 0  # type: ignore
        and len(unstaged) == 0  # type: ignore
        and len(untracked) == 0  # type: ignore
    )


def has_commits(cwd: Path) -> bool:
    try:
        Repo(str(cwd)).head()
        return True
    except KeyError:
        return False


def init(cwd: Path) -> None:
    Repo.init(str(cwd), default_branch=b"main")  # type: ignore


def add(cwd: Path, name: Path) -> None:
    porcelain.add(str(cwd), str(name))  # type: ignore


def commit_initial(cwd: Path) -> None:
    porcelain.commit(str(cwd), message=b"Initial commit")  # type: ignore


def commit(cwd: Path, commit_info: CommitInfo) -> None:
    full_message = commit_info.message + "\n\n" + commit_info.description
    Repo(str(cwd)).do_commit(  # type: ignore
        message=_encode(full_message),
        author=_encode(commit_info.author),
        author_timestamp=commit_info.date,
    )


def _encode(value: str) -> bytes:
    return value.encode("utf-8")
