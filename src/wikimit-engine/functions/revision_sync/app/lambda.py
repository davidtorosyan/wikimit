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

    if not title:
        return {
            "success": False,
            "message": "Invalid event, missing title",
        }

    request = SyncRequest(
        site=SITE_WIKIPEDIA,
        language=LANGUAGE_EN,
        title=title,
        reset=reset,
    )
    result = sync(request)

    max_iterations_reached = (
        result.needs_sync is True and iteration + 1 >= MAX_ITERATIONS
    )

    return {
        "success": True,
        "newly_synced_revisions": result.newly_synced_revisions,
        "last_sync": result.last_sync,
        "needs_sync": result.needs_sync,
        "max_iterations_reached": max_iterations_reached,
        "synced_revision_timestamp": result.synced_revision_timestamp,
        "iteration": iteration + 1,
        "title": title,
        "total_revisions": result.total_revisions,
        "synced_revisions": result.synced_revisions,
    }
