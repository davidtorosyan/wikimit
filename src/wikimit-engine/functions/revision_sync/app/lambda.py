import traceback
from typing import Any

from .sync import MAX_ITERATIONS, SyncRequest, sync
from .wiki import LANGUAGE_EN, SITE_WIKIPEDIA


def lambda_handler(event: Any, context: object) -> Any:  # type: ignore
    try:
        return _lambda_handler_internal(event, context)
    except Exception as e:
        return {
            "success": False,
            "message": "Unexpected error",
            "exception": str(e),
            "stacktrace": "".join(
                traceback.format_exception(type(e), e, e.__traceback__)
            ),
        }


def _lambda_handler_internal(event: Any, context: object) -> Any:  # type: ignore
    title = event.get("title")
    iteration = event.get("iteration", 0)
    reset = event.get("reset", False)

    if not event:
        return {
            "success": False,
            "message": "Invalid event, missing title",
        }

    if iteration >= MAX_ITERATIONS:
        synced_revisions = event.get("synced_revisions", 0)
        total_revisions = event.get("total_revisions", 0)
        return {
            "success": False,
            "message": f"Max iterations ({MAX_ITERATIONS}) reached. So far synced {synced_revisions} revisions out of {total_revisions}.",
            "title": title,
        }

    request = SyncRequest(
        site=SITE_WIKIPEDIA,
        language=LANGUAGE_EN,
        title=title,
        reset=reset,
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
        "total_revisions": result.total_revisions,
        "synced_revisions": result.synced_revisions,
    }
