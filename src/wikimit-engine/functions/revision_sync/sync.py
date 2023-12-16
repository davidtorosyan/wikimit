from dataclasses import dataclass

from wiki import current_page_info


@dataclass
class SyncRequest:
    site: str
    language: str
    title: str


@dataclass
class SyncResult:
    has_new_revisions: bool


def sync(request: SyncRequest) -> SyncResult:
    info = current_page_info(request.title, request.site, request.language)
    print(info)
    return SyncResult(has_new_revisions=False)
