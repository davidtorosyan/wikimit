import responses
from functions.revision_sync.app import wiki
from responses import _recorder

MOCK_TITLE = "Finch"
MOCK_SITE = "wikipedia.org"
MOCK_LANG = "en"

MOCK_SMOKE_CURRENT_PATH = "tests/mock/wiki_smoke_current.yaml"
MOCK_SMOKE_HISTORY_1_PATH = "tests/mock/wiki_smoke_history_1.yaml"
MOCK_SMOKE_HISTORY_2_PATH = "tests/mock/wiki_smoke_history_2.yaml"

SMOKE_LIMIT = 5
SMOKE_OFFSET_1 = "2003-04-03T15:57:37Z"
SMOKE_OFFSET_2 = "2003-05-14T06:17:45Z"


MOCK_PAGE_INFO = wiki.PageInfo(
    id="some id",
    title=MOCK_TITLE,
    url=f"https://${MOCK_SITE}/wiki/some_title",
    site=MOCK_SITE,
    language=MOCK_LANG,
    highest_known_revision_id="1186000588",
    highest_known_revision_timestamp="2023-11-20T08:31:12Z",
)


@responses.activate
def test_get_page_info():
    responses._add_from_file(file_path=MOCK_SMOKE_CURRENT_PATH)
    info = wiki.get_page_info(MOCK_TITLE)
    assert info.title == MOCK_TITLE
    assert info.url == "https://en.wikipedia.org/wiki/Finch"
    assert info.language == MOCK_LANG
    assert info.highest_known_revision_id == "1186000588"
    assert info.highest_known_revision_timestamp == "2023-11-20T08:31:12Z"


@responses.activate
def test_get_revisions_1():
    responses._add_from_file(file_path=MOCK_SMOKE_HISTORY_1_PATH)
    revisions = wiki.get_revisions(MOCK_PAGE_INFO, limit=SMOKE_LIMIT)
    assert len(revisions) == SMOKE_LIMIT
    assert revisions[-1].timestamp == SMOKE_OFFSET_1


@responses.activate
def test_get_revisions_2():
    responses._add_from_file(file_path=MOCK_SMOKE_HISTORY_2_PATH)
    revisions = wiki.get_revisions(
        MOCK_PAGE_INFO, offset=SMOKE_OFFSET_1, limit=SMOKE_LIMIT
    )
    assert len(revisions) == SMOKE_LIMIT
    assert revisions[-1].timestamp == SMOKE_OFFSET_2


@_recorder.record(file_path=MOCK_SMOKE_CURRENT_PATH)
def record_smoke_current():
    """
    Run this function to record the responses for the smoke test.
    """
    wiki.get_page_info(MOCK_TITLE)


@_recorder.record(file_path=MOCK_SMOKE_HISTORY_1_PATH)
def record_smoke_history_1():
    """
    Run this function to record the responses for the smoke test.
    """
    wiki.get_revisions(MOCK_PAGE_INFO, limit=SMOKE_LIMIT)


@_recorder.record(file_path=MOCK_SMOKE_HISTORY_2_PATH)
def record_smoke_history_2():
    """
    Run this function to record the responses for the smoke test.
    """
    wiki.get_revisions(MOCK_PAGE_INFO, offset="2003-04-03T15:57:37Z", limit=SMOKE_LIMIT)
