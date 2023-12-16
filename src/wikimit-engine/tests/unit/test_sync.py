from functions.revision_sync import sync

MOCK_SITE = "somewiki.org"
MOCK_LANG = "somelang"
MOCK_TITLE = "some title"


def test_sync():
    result = sync.sync(sync.SyncRequest(MOCK_SITE, MOCK_LANG, MOCK_TITLE))
    assert result.has_new_revisions == False
