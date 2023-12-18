import json
from dataclasses import dataclass
from pathlib import Path

from .git import (
    CommitInfo,
    add,
    commit,
    commit_initial,
    has_commits,
    init,
    is_clean,
    repo_root,
)
from .serialize import convert_json
from .text import LICENSE_CC_BY_SA, README_TEMPLATE

ARTICLE_NAME = "article.xml"
INFO_NAME = "info.json"
README_NAME = "README.md"
LICENSE_NAME = "LICENSE"


@dataclass
class RepoInfo:
    id: str
    url: str
    title: str
    site: str
    language: str
    highest_known_revision_id: str
    highest_known_revision_timestamp: str
    synced_revision_id: str
    synced_revision_timestamp: str
    last_sync: str


def initialize(path: Path, init_info: RepoInfo) -> RepoInfo:
    # existence
    if not path.exists():
        path.mkdir(parents=True)
    # git repo
    root = repo_root(path)
    if root == "":
        init(path)
    else:
        assert Path(root) == path
    # status
    assert is_clean(path)
    # files
    article_file = path / ARTICLE_NAME
    info_file = path / INFO_NAME
    readme_file = path / README_NAME
    license_file = path / LICENSE_NAME
    if not has_commits(path):
        article_file.touch()
        info_file.write_text(convert_json(init_info))
        readme_file.write_text(README_TEMPLATE.format(init_info.title, init_info.url))
        license_file.write_text(LICENSE_CC_BY_SA)
        add(path, article_file)
        add(path, info_file)
        add(path, readme_file)
        add(path, license_file)
        commit_initial(path)
    else:
        assert article_file.exists()
        assert info_file.exists()
        assert readme_file.exists()
        assert license_file.exists()
    # info
    content = json.loads(info_file.read_text())
    return RepoInfo(**content)


def apply_commit(
    path: Path, repo_info: RepoInfo, commit_info: CommitInfo, text: str
) -> None:
    article_file = path / ARTICLE_NAME
    article_file.write_text(text)

    info_file = path / INFO_NAME
    info_file.write_text(convert_json(repo_info))

    add(path, article_file)
    add(path, info_file)
    commit(path, commit_info)
