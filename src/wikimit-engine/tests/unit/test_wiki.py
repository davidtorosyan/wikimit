from functions.revision_sync import wiki


def test_current_page_info():
    info = wiki.current_page_info("Finch")

    assert info.title == "Finch"
