import copy
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .git import CommitInfo
from .repo import RepoInfo, apply_commit, initialize
from .wiki import PageInfo, Revision, get_edit_count, get_page_info, get_revisions

REPO_BASE_PATH = Path("/tmp/wikimit/repos")
SYNC_LIMIT = 5
MAX_ITERATIONS = 3


@dataclass
class SyncRequest:
    site: str
    language: str
    title: str
    reset: bool


@dataclass
class SyncResult:
    newly_synced_revisions: int
    last_sync: str
    needs_sync: bool
    synced_revision_timestamp: str
    total_revisions: int
    synced_revisions: int


def sync(request: SyncRequest) -> SyncResult:
    page_info = get_page_info(request.title, request.site, request.language)
    path = REPO_BASE_PATH / _get_repo_name(page_info)
    repo_info = initialize(path, _init_repo_info(page_info), request.reset)
    revisions = (
        get_revisions(
            page_info,
            offset_timestamp=repo_info.synced_revision_timestamp,
            limit=SYNC_LIMIT,
        )
        if _needs_sync(page_info, repo_info)
        else []
    )

    is_revision_count_outdated = (
        repo_info.highest_known_revision_id != page_info.highest_known_revision_id
    )
    updated_repo_info = _update_repo_info_with_pageinfo(repo_info, page_info)
    for revision in revisions:
        is_first_revision = repo_info.first_revision_id == ""
        commit_info = _to_commit_info(revision)
        updated_repo_info = _update_repo_info_with_revision(updated_repo_info, revision)
        if is_revision_count_outdated or is_first_revision:
            total_revisions = get_edit_count(
                page_info,
                from_revision_id=updated_repo_info.first_revision_id,
                to_revision_id=page_info.highest_known_revision_id,
            )
            updated_repo_info = _update_repo_info_with_total_revisions(
                updated_repo_info, total_revisions
            )
        apply_commit(path, updated_repo_info, commit_info, revision.text)

    return SyncResult(
        newly_synced_revisions=len(revisions),
        last_sync=updated_repo_info.last_sync,
        needs_sync=_needs_sync(page_info, updated_repo_info),
        synced_revision_timestamp=updated_repo_info.synced_revision_timestamp,
        total_revisions=updated_repo_info.known_total_revisions,
        synced_revisions=updated_repo_info.synced_revisions,
    )


def _needs_sync(page_info: PageInfo, repo_info: RepoInfo) -> bool:
    return repo_info.synced_revision_id != page_info.highest_known_revision_id


def _get_repo_name(page: PageInfo) -> str:
    return f"{page.language}.{page.title}"


def _init_repo_info(info: PageInfo) -> RepoInfo:
    return RepoInfo(
        id=info.id,
        url=info.url,
        title=info.title,
        site=info.site,
        language=info.language,
        highest_known_revision_id=info.highest_known_revision_id,
        highest_known_revision_timestamp=info.highest_known_revision_timestamp,
        synced_revision_id="",
        synced_revision_timestamp="",
        last_sync=_current_time(),
        synced_revisions=0,
        first_revision_id="",
        known_total_revisions=0,
    )


def _update_repo_info_with_pageinfo(info: RepoInfo, pageInfo: PageInfo) -> RepoInfo:
    updated = copy.copy(info)
    updated.highest_known_revision_id = pageInfo.highest_known_revision_id
    updated.highest_known_revision_timestamp = pageInfo.highest_known_revision_timestamp
    return updated


def _update_repo_info_with_total_revisions(
    info: RepoInfo, total_revisions: int
) -> RepoInfo:
    updated = copy.copy(info)
    updated.known_total_revisions = total_revisions
    return updated


def _update_repo_info_with_revision(info: RepoInfo, revision: Revision) -> RepoInfo:
    updated = copy.copy(info)
    updated.synced_revision_id = revision.id
    updated.synced_revision_timestamp = revision.timestamp
    updated.last_sync = _current_time()
    updated.synced_revisions += 1
    if updated.first_revision_id == "":
        updated.first_revision_id = revision.id
    return updated


def _to_commit_info(revision: Revision) -> CommitInfo:
    author = (
        f"{revision.contributor_username} <{revision.contributor_id}>"
        if revision.contributor_username
        else f"{revision.contributor_ip} <IP>"
    )
    info = OrderedDict(
        [
            ("id", revision.id),
            ("timestamp", revision.timestamp),
            ("contributor_username", revision.contributor_username),
            ("contributor_id", revision.contributor_id),
            ("contributor_ip", revision.contributor_ip),
            ("minor", "True" if revision.minor else "False"),
            ("model", revision.model),
            ("format", revision.format),
            ("sha1", revision.sha1),
        ]
    )
    description = "\n".join(["{}: {}".format(k, v) for k, v in info.items() if v])

    timestamp_dt = datetime.fromisoformat(revision.timestamp.rstrip("Z"))
    unix_time = int(time.mktime(timestamp_dt.timetuple()))

    return CommitInfo(
        message=revision.comment,
        author=author,
        description=description,
        date=unix_time,
    )


def _current_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
