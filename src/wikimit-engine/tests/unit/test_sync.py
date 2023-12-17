from functions.revision_sync.app import sync, wiki
from pytest_mock import MockFixture

MOCK_SITE = "somewiki.org"
MOCK_LANG = "somelang"
MOCK_TITLE = "some title"

MOCK_PAGE_INFO = wiki.PageInfo(
    id="some id",
    title=MOCK_TITLE,
    url=f"https://${MOCK_SITE}/wiki/some_title",
    language=MOCK_LANG,
    highest_known_revision_id="123",
    highest_known_revision_timestamp="2023-11-20T08:31:12Z",
)


def test_sync(mocker: MockFixture):
    # setup
    mock_wiki = mocker.patch(
        "functions.revision_sync.app.sync.current_page_info",
        return_value=MOCK_PAGE_INFO,
    )

    # run
    result = sync.sync(sync.SyncRequest(MOCK_SITE, MOCK_LANG, MOCK_TITLE))

    # verify
    assert result.has_new_revisions == False
    mock_wiki.assert_called_once_with(MOCK_TITLE, MOCK_SITE, MOCK_LANG)
