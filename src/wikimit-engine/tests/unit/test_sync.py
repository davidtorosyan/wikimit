from functions.revision_sync.app import repo, sync, wiki
from pytest_mock import MockFixture

MOCK_SITE = "somewiki.org"
MOCK_LANG = "somelang"
MOCK_TITLE = "some title"

MOCK_SYNCED_REVISION_TIMESTAMP = "some synced revision timestamp"
MOCK_LAST_SYNC = "some last sync timestamp"
MOCK_HIGHEST_ID = "some high id"

MOCK_PAGE_INFO = wiki.PageInfo(
    id="pageInfoId",
    title=MOCK_TITLE,
    url="pageInfoUrl",
    site=MOCK_SITE,
    language=MOCK_LANG,
    highest_known_revision_id=MOCK_HIGHEST_ID,
    highest_known_revision_timestamp="pageInfoTimestamp",
)

MOCK_REPO_INFO_ALREADY_SYNCED = repo.RepoInfo(
    id="repoInfoId",
    title=MOCK_TITLE,
    url="repoInfoUrl",
    site=MOCK_SITE,
    language=MOCK_LANG,
    highest_known_revision_id="repoInfoHighestId",
    highest_known_revision_timestamp="repoInfoHighestTimestamp",
    synced_revision_id=MOCK_HIGHEST_ID,
    synced_revision_timestamp=MOCK_SYNCED_REVISION_TIMESTAMP,
    last_sync=MOCK_LAST_SYNC,
)


def test_sync_already_synced(mocker: MockFixture):
    # setup
    mock_get_page_info = mocker.patch(
        "functions.revision_sync.app.sync.get_page_info",
        return_value=MOCK_PAGE_INFO,
    )
    mock_initialize = mocker.patch(
        "functions.revision_sync.app.sync.initialize",
        return_value=MOCK_REPO_INFO_ALREADY_SYNCED,
    )

    # run
    result = sync.sync(sync.SyncRequest(MOCK_SITE, MOCK_LANG, MOCK_TITLE))

    # verify
    assert result.newly_synced_revisions == 0
    assert result.newly_synced_revisions == 0
    assert result.last_sync == MOCK_LAST_SYNC
    assert result.synced_revision_timestamp == MOCK_SYNCED_REVISION_TIMESTAMP
    mock_get_page_info.assert_called_once()
    mock_initialize.assert_called_once()
