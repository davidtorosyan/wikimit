from functions.revision_sync.app import sync
from pytest_mock import MockFixture

MOCK_SITE = "somewiki.org"
MOCK_LANG = "somelang"
MOCK_TITLE = "some title"


def test_sync(mocker: MockFixture):
    # mocker.patch.object(wiki, "current_page_info", None)

    result = sync.sync(sync.SyncRequest(MOCK_SITE, MOCK_LANG, MOCK_TITLE))
    assert result.has_new_revisions == False
