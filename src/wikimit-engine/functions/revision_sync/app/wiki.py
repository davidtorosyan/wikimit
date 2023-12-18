from dataclasses import dataclass
from xml.dom.minidom import Document, Element, parseString

import requests


@dataclass
class PageInfo:
    id: str
    url: str
    title: str
    site: str
    language: str
    highest_known_revision_id: str
    highest_known_revision_timestamp: str


@dataclass
class Revision:
    id: str
    contributor_username: str
    contributor_id: str
    contributor_ip: str
    comment: str
    timestamp: str
    minor: bool
    model: str
    format: str
    sha1: str
    text: str


SITE_WIKIPEDIA = "wikipedia.org"
LANGUAGE_EN = "en"


def get_page_info(
    title: str, site: str = SITE_WIKIPEDIA, language: str = LANGUAGE_EN
) -> PageInfo:
    content = _export_page(site, language, title, current=True)
    return _parse_page_info(site, language, content)


def get_revisions(
    page_info: PageInfo,
    offset: str,
    limit: int = 5,
) -> list[Revision]:
    content = _export_page(
        page_info.site, page_info.language, page_info.title, offset=offset, limit=limit
    )
    return _parse_revisions(content)


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
        site=site,
        language=language,
        highest_known_revision_id=highest_id,
        highest_known_revision_timestamp=highest_timestamp,
    )


def _parse_revisions(content: bytes) -> list[Revision]:
    doc = parseString(content)
    revisions = doc.getElementsByTagName("revision")
    return [_parse_revision(r) for r in revisions]


def _parse_revision(revision: Element) -> Revision:
    contributor = _find_node(revision, "contributor")
    contributor_username = _extract_text(contributor, "username")
    contributor_id = _extract_text(contributor, "id")
    contributor_ip = _extract_text(contributor, "ip")

    id = _extract_text(revision, "id")
    comment = _extract_text(revision, "comment")
    timestamp = _extract_text(revision, "timestamp")
    minor = _has_child(revision, "minor")
    model = _extract_text(revision, "model")
    format = _extract_text(revision, "format")
    sha1 = _extract_text(revision, "sha1")

    text = _extract_text(revision, "text")

    return Revision(
        id=id,
        contributor_username=contributor_username,
        contributor_id=contributor_id,
        contributor_ip=contributor_ip,
        comment=comment,
        timestamp=timestamp,
        minor=minor,
        model=model,
        format=format,
        sha1=sha1,
        text=text,
    )


def _export_page(
    site: str,
    language: str,
    title: str,
    current: bool = False,
    offset: str = "",
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


def _has_child(node: Element, tag: str):
    elems = node.getElementsByTagName(tag)
    return len(elems) > 0


def _find_node(doc: Document | Element, tag: str) -> Element:
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
