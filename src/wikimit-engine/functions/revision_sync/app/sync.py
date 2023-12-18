from dataclasses import dataclass
from pathlib import Path

from .repo import initialize
from .wiki import PageInfo, current_page_info

REPO_BASE_PATH = Path("/tmp/wikimit/repos")


@dataclass
class SyncRequest:
    site: str
    language: str
    title: str


@dataclass
class SyncResult:
    has_new_revisions: bool


def sync(request: SyncRequest) -> SyncResult:
    page_info = current_page_info(request.title, request.site, request.language)
    path = REPO_BASE_PATH / _get_repo_name(page_info)
    repo_info = initialize(path, page_info)
    print(page_info)
    print(repo_info)
    return SyncResult(has_new_revisions=False)


def _get_repo_name(page: PageInfo) -> str:
    return f"{page.language}.{page.title}"
