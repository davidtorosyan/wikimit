from typing import Any

from .sync import SyncRequest, sync
from .wiki import LANGUAGE_EN, SITE_WIKIPEDIA


def lambda_handler(event: Any, context: object) -> Any:  # type: ignore
    if "title" not in event:
        return {
            "success": False,
            "message": "Invalid event, missing title",
            "has_new_revisions": False,
        }

    request = SyncRequest(
        site=SITE_WIKIPEDIA,
        language=LANGUAGE_EN,
        title=event.get("title"),  # type: ignore
    )
    result = sync(request)

    return {
        "success": True,
        "has_new_revisions": result.has_new_revisions,
    }
