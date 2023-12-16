from dataclasses import dataclass
from xml.dom.minidom import Document, Element, parseString

import requests


@dataclass
class PageInfo:
    id: str
    url: str
    title: str
    language: str
    highest_known_revision_id: str
    highest_known_revision_timestamp: str


WIKI_BASE = "https://en.wikipedia.org"

SITE_WIKIPEDIA = "wikipedia.org"
LANGUAGE_EN = "en"


def current_page_info(
    title: str, site: str = SITE_WIKIPEDIA, language: str = LANGUAGE_EN
) -> PageInfo:
    content = _export_page(site, language, title, current=True)
    return _parse_page_info(site, language, content)


def _parse_page_info(site: str, language: str, content: bytes) -> PageInfo:
    doc = parseString(content)

    page = _find_node(doc, "page")
    title = _extract_text(page, "title")
    id = _extract_text(page, "id")

    revision = _find_node(doc, "revision")
    highest_id = _extract_text(revision, "id")
    highest_timestamp = _extract_text(revision, "timestamp")

    base_url = _compose_url(site, language)
    url = "{}/wiki/{}".format(base_url, title)
    return PageInfo(
        id=id,
        url=url,
        title=title,
        language=language,
        highest_known_revision_id=highest_id,
        highest_known_revision_timestamp=highest_timestamp,
    )


def _export_page(
    site: str,
    language: str,
    title: str,
    current: bool = False,
    offset: int = 1,
    limit: int = 5,
) -> bytes:
    """
    Download the history of a page from Wikipedia.

    See parameters here:
    https://www.mediawiki.org/wiki/Manual:Parameters_to_Special:Export
    """
    base_url = _compose_url(site, language)
    api_url = f"{base_url}/w/index.php"
    params = {
        "title": "Special:Export",
        "pages": title,
        "action": "submit",
        "curonly": current,
        "offset": offset,
        "limit": limit,
    }
    response = requests.post(api_url, params=params)
    return response.content


def _compose_url(site: str, language: str) -> str:
    return f"https://{language}.{site}"


# def _has_child(node: Element, tag: str):
#     elems = node.getElementsByTagName(tag)
#     return len(elems) > 0


def _find_node(doc: Document, tag: str) -> Element:
    return doc.getElementsByTagName(tag)[0]


def _extract_text(node: Element, tag: str):
    elems = node.getElementsByTagName(tag)
    return _get_text(elems[0].childNodes) if elems else ""


def _get_text(nodelist: list[Element]):
    results: list[str] = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            results.append(node.data)  # type: ignore
    return "".join(results)
