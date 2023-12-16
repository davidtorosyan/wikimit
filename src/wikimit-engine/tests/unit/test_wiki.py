import responses
from functions.revision_sync import wiki
from responses import _recorder

MOCK_TITLE = "Finch"
MOCK_SMOKE_CURRENT_PATH = "tests/mock/wiki_smoke_current.yaml"


@responses.activate
def test_current_page_info():
    responses._add_from_file(file_path=MOCK_SMOKE_CURRENT_PATH)
    info = wiki.current_page_info(MOCK_TITLE)
    assert info.title == MOCK_TITLE


@_recorder.record(file_path=MOCK_SMOKE_CURRENT_PATH)
def record_smoke_current():
    """
    Run this function to record the responses for the smoke test.
    """
    wiki.current_page_info(MOCK_TITLE)
