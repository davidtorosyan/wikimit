from typing import Any

from .sync import MAX_ITERATIONS, SyncRequest, sync
from .wiki import LANGUAGE_EN, SITE_WIKIPEDIA


def lambda_handler(event: Any, context: object) -> Any:  # type: ignore
    title = event.get("title")
    iteration = event.get("iteration", 0)

    if not event:
        return {
            "success": False,
            "message": "Invalid event, missing title",
        }

    if iteration >= MAX_ITERATIONS:
        return {
            "success": False,
            "message": f"Max iterations ({MAX_ITERATIONS}) reached",
            "title": title,
        }

    request = SyncRequest(
        site=SITE_WIKIPEDIA,
        language=LANGUAGE_EN,
        title=title,
    )
    result = sync(request)

    return {
        "success": True,
        "newly_synced_revisions": result.newly_synced_revisions,
        "last_sync": result.last_sync,
        "needs_sync": result.needs_sync,
        "synced_revision_timestamp": result.synced_revision_timestamp,
        "iteration": iteration + 1,
        "title": title,
    }
