import datetime
import json
from dataclasses import dataclass
from pathlib import Path

from .git import add, commit_initial, has_commits, init, is_clean, repo_root
from .serialize import convert_json
from .text import LICENSE_CC_BY_SA, README_TEMPLATE
from .wiki import PageInfo

ARTICLE_NAME = "article.xml"
INFO_NAME = "info.json"
README_NAME = "README.md"
LICENSE_NAME = "LICENSE"


@dataclass
class RepoInfo:
    id: str
    url: str
    title: str
    language: str
    highest_known_revision_id: str
    highest_known_revision_timestamp: str
    synced_revision_id: str
    synced_revision_timestamp: str
    last_sync: str


def _current_time() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _init_sync_info(info: PageInfo) -> RepoInfo:
    return RepoInfo(
        id=info.id,
        url=info.url,
        title=info.title,
        language=info.language,
        highest_known_revision_id=info.highest_known_revision_id,
        highest_known_revision_timestamp=info.highest_known_revision_timestamp,
        synced_revision_id="",
        synced_revision_timestamp="",
        last_sync=_current_time(),
    )


def initialize(path: Path, info: PageInfo) -> RepoInfo:
    # existence
    if not path.exists():
        path.mkdir(parents=True)
    # git repo
    root = repo_root(path)
    if root == "":
        init(path)
    elif root != path:
        raise Exception(f"Path {path} is in a git repository, but is not the root")
    # status
    assert is_clean(path)
    # files
    article_file = path / ARTICLE_NAME
    info_file = path / INFO_NAME
    readme_file = path / README_NAME
    license_file = path / LICENSE_NAME
    if not has_commits(path):
        article_file.touch()
        info_file.write_text(convert_json(_init_sync_info(info)))
        readme_file.write_text(README_TEMPLATE.format(info.title, info.url))
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
    return json.loads(info_file.read_text())
