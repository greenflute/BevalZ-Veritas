"""Reference section parsing and query-building helpers."""

import hashlib
import html
import re

from .text_utils import _brief_text, _normalize_title, _title_tokens

__all__ = [
    "REFERENCE_CONTAINER_WORD_RE",
    "split_references_from_text",
    "parse_references",
    "_truncate_reference_suffix",
    "_reference_items_from_numbered_lines",
    "_looks_like_reference_table_noise",
    "_clean_reference_text",
    "_normalize_doi",
    "_looks_like_reference_container_part",
    "_looks_like_reference_author_fragment",
    "_name_tokens",
    "_author_similarity",
    "_reference_year",
    "extract_reference_year_hint",
    "extract_reference_author_hint",
    "extract_reference_container_hint",
    "extract_reference_title",
    "build_reference_query",
    "reference_cache_key",
]


def split_references_from_text(text):
    """Remove reference sections from main audit text and return parsed tail text."""
    text = str(text or "")
    pattern = re.compile(
        r"(?im)^(?:\[\[BLOCK[^\]]*\]\]\s*)?(?:#+\s*)?(?:references?|bibliography|参考文献|参考资料|works cited)\s*(?:\[\[/BLOCK\]\]\s*)?$"
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return text, ""
    start = matches[-1].start()
    main_text = text[:start].rstrip()
    references_text = text[start:].strip()
    return main_text, references_text


def parse_references(references_text):
    text = _clean_reference_text(references_text)
    text = _truncate_reference_suffix(text)
    text = re.sub(r"(?im)^(?:#+\s*)?(?:references?|bibliography|参考文献|参考资料|works cited)\s*$", "", text).strip()
    if not text:
        return []
    raw_items = _reference_items_from_numbered_lines(text)
    if len(raw_items) <= 1:
        raw_items = re.split(r"\n{2,}", text)
    refs = []
    for item in raw_items:
        item = re.sub(r"\s+", " ", item).strip()
        item = re.sub(r"^(?:\[\d+\]|\d+\.|\(\d+\))\s*", "", item)
        item = re.sub(r"^\d+\.\s*", "", item)
        if len(item) < 8:
            continue
        if _looks_like_reference_table_noise(item):
            continue
        doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", item, re.IGNORECASE)
        year = extract_reference_year_hint(item)
        has_journal_hint = bool(re.search(r"\b(?:journal|j\.|proc\.|nature|science|cell|ieee|acm|springer|elsevier|frontiers|plos|bmc|lancet)\b", item, re.IGNORECASE))
        doi = _normalize_doi(doi_match.group(0)) if doi_match else ""
        refs.append({
            "text": item,
            "doi": doi,
            "year": year,
            "has_journal_hint": has_journal_hint,
            "title_hint": extract_reference_title(item),
            "author_hint": extract_reference_author_hint(item),
            "container_hint": extract_reference_container_hint(item),
        })
    return refs


def _truncate_reference_suffix(text):
    """Drop non-reference sections accidentally captured after References."""
    text = str(text or "")
    suffix_heading = re.search(
        r"(?im)^\s*(?:figure\s+legends?|figures?|tables?|supplementary\s+(?:material|information)|acknowledg(?:e)?ments?)\s*$",
        text,
    )
    if suffix_heading:
        return text[:suffix_heading.start()].rstrip()
    return text


def _reference_items_from_numbered_lines(text):
    """Build reference items while tolerating MinerU per-page list numbering."""
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    items = []
    current = []
    expected_number = 1

    def flush():
        nonlocal current
        if current:
            items.append(" ".join(current).strip())
            current = []

    for line in lines:
        if re.fullmatch(r"(?i)(?:article\s+in\s+press|references?|bibliography|参考文献|参考资料|works cited)", line):
            continue
        bracketed = re.match(r"^\[(\d+)\]\s*(.+)$", line)
        if bracketed:
            visible_number = int(bracketed.group(1))
            body = bracketed.group(2).strip()
        else:
            numbered = re.match(r"^(\d+)\.\s*(.+)$", line)
            if not numbered:
                if current:
                    current.append(line)
                continue
            local_number = int(numbered.group(1))
            rest = numbered.group(2).strip()
            nested = re.match(r"^(\d+)\.?\s*(.+)$", rest)
            if nested:
                visible_number = int(nested.group(1))
                body = nested.group(2).strip()
            else:
                visible_number = local_number
                body = rest

        if not current or visible_number == expected_number:
            flush()
            current = [body]
            expected_number = visible_number + 1
        else:
            current.append(body)
    flush()
    return items


def _looks_like_reference_table_noise(item):
    """Avoid treating extracted tables as reference entries."""
    decoded = html.unescape(str(item or "")).strip()
    lowered = decoded.lower()
    if "[[table_start" in lowered or "[[table_continuation" in lowered:
        return True
    td_count = len(re.findall(r"</?t[dh]\b", lowered))
    tr_count = len(re.findall(r"</?tr\b", lowered))
    if "<table" in lowered and (td_count >= 4 or tr_count >= 2):
        return True
    pipe_cells = sum(1 for line in decoded.splitlines() if line.count("|") >= 3)
    if pipe_cells >= 2 and not re.search(r"\b(?:doi|pmid|arxiv|journal|volume|issue)\b", decoded, re.I):
        return True
    return False


def _clean_reference_text(text):
    text = str(text or "")
    text = re.sub(r"\[\[EXTRACTION_NOTE\]\].*?\[\[/EXTRACTION_NOTE\]\]", "\n", text, flags=re.S)
    text = re.sub(r"\[\[/?(?:BLOCK|FIGURE)[^\]]*\]\]", "\n", text, flags=re.I)
    text = re.sub(r"\[\[TABLE_START[^\]]*\]\]|\[\[TABLE_END\]\]|\[\[TABLE_CONTINUATION[^\]]*\]\]", "\n", text)
    text = re.sub(r"(?m)^===\s*文件:.*?===\s*$", "\n", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_doi(value):
    value = html.unescape(str(value or "")).strip()
    value = re.sub(r"(?i)^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"(?i)^doi\s*[:：]\s*", "", value)
    value = value.strip().rstrip(".,;)]}")
    return value.lower()


REFERENCE_CONTAINER_WORD_RE = re.compile(
    r"\b(?:journal|jclin|proc\.?|proceedings|nature|science|cell|frontiers|plos|bmc|"
    r"lancet|thyroid|oncology|endocrinology|communications?|commun|annals|cancers|"
    r"cancer\s+letters?|cancer\s+lett|mol\s+cancer|jama|esmo)\b",
    re.I,
)


def _looks_like_reference_container_part(part):
    part = str(part or "").strip()
    if not REFERENCE_CONTAINER_WORD_RE.search(part):
        return False
    normalized = _normalize_title(part)
    known_short = {
        "ca cancer jclin",
        "nat commun",
        "mol cancer",
        "cancer lett",
        "cancer letters",
        "jama",
        "the lancet",
        "thyroid",
        "cancers basel",
        "esmo open",
    }
    if normalized in known_short:
        return True
    if len(_title_tokens(part)) > 6:
        return False
    return bool(re.search(
        r"\b(?:vol\.?|volume)\b|\b\d+\s*,|\b\d+\s+\d+|\(\d{4}\)|\b\d{1,5}\s*[-–]\s*\d{1,5}\b",
        part,
        re.I,
    ))


def _looks_like_reference_author_fragment(part):
    part = str(part or "").strip()
    if not part:
        return False
    if re.fullmatch(r"(?:[A-Z]\.?){1,4}", part):
        return True
    if re.search(r"\bet\s+al\b", part, re.I):
        return True
    if re.search(r"(?:^|[\s,&])(?:[A-Z]\.){1,3}(?:,|\s|$)", part):
        return True
    if re.search(r"\b[A-Z][A-Za-z'’-]+,\s*[A-Z](?:\.|$)", part):
        return True
    return False


def _name_tokens(value):
    return {
        token
        for token in re.findall(r"[a-z\u4e00-\u9fff]+", _normalize_title(value))
        if len(token) >= 3
    }


def _author_similarity(query_author, match_authors):
    left = _name_tokens(query_author)
    if not left:
        return 0.0
    right = set()
    for author in match_authors or []:
        right.update(_name_tokens(author))
    if not right:
        return 0.0
    return len(left & right) / max(len(left), 1)


def _reference_year(ref):
    if isinstance(ref, dict):
        value = ref.get("year") or ref.get("publication_year") or ""
    else:
        value = str(ref or "")
    match = re.search(r"\b(19|20)\d{2}\b", str(value))
    return match.group(0) if match else ""


def extract_reference_year_hint(text):
    text = str(text or "")
    parenthetical = re.findall(r"\(((?:19|20)\d{2})\)", text)
    if parenthetical:
        return parenthetical[-1]
    years = re.findall(r"\b((?:19|20)\d{2})\b", text)
    return years[-1] if years else ""


def extract_reference_author_hint(text):
    text = re.sub(r"^(?:\[\d+\]|\d+\.|\(\d+\))\s*", "", str(text or "")).strip()
    before_year = re.split(r"\b(?:19|20)\d{2}\b", text, maxsplit=1)[0]
    before_title = before_year.split(".")[0] if "." in before_year else before_year
    names = re.findall(r"\b[A-Z][A-Za-z'’-]{2,}\b", before_title)
    return " ".join(names[:3])


def extract_reference_container_hint(text):
    text = re.sub(r"^(?:\[\d+\]|\d+\.|\(\d+\))\s*", "", str(text or "")).strip()
    text = re.sub(r"https?://\S+", "", text, flags=re.I)
    parts = [p.strip(" .;:") for p in re.split(r"\.\s+", text) if p.strip(" .;:")]
    for part in parts:
        if _looks_like_reference_author_fragment(part):
            continue
        if len(_title_tokens(part)) > 8:
            continue
        if _looks_like_reference_container_part(part):
            container = re.split(r"\b(?:vol\.?|volume|\d+\s*,|\d+\s+\d|\(\d{4}\))", part, maxsplit=1, flags=re.I)[0]
            return container.strip(" .;:")[:160]
    return ""


def extract_reference_title(text):
    text = re.sub(r"^(?:\[\d+\]|\d+\.|\(\d+\))\s*", "", str(text or "")).strip()
    text = re.sub(r"\bdoi\s*[:：]?\s*10\.\S+", "", text, flags=re.I).strip()
    text = re.sub(r"https?://\S+", "", text, flags=re.I).strip()
    parts = [p.strip(" .;:") for p in re.split(r"\.\s+", text) if p.strip(" .;:")]
    if not parts:
        return _brief_text(text, 160)
    candidates = []
    for part in parts:
        if _looks_like_reference_author_fragment(part):
            continue
        if _looks_like_reference_container_part(part):
            continue
        if len(_title_tokens(part)) >= 2:
            candidates.append(part)
    if candidates:
        return candidates[0][:360]
    return parts[min(1, len(parts) - 1)][:360]


def build_reference_query(ref):
    title = ref.get("title_hint") or extract_reference_title(ref.get("text", ""))
    author = ref.get("author_hint") or extract_reference_author_hint(ref.get("text", ""))
    year = _reference_year(ref)
    doi = _normalize_doi(ref.get("doi", ""))
    container = ref.get("container_hint") or extract_reference_container_hint(ref.get("text", ""))
    query_parts = [p for p in (title, author, year, container) if p]
    bibliographic = " ".join(query_parts) or ref.get("text", "")[:240]
    if not doi and ref.get("text"):
        bibliographic = ref.get("text", "")[:600]
    return {
        "doi": doi,
        "title": title,
        "author": author,
        "container": container,
        "year": year,
        "bibliographic": bibliographic,
    }


def reference_cache_key(ref):
    query = build_reference_query(ref)
    if query.get("doi"):
        return "doi:" + query["doi"]
    key = f"{_normalize_title(query.get('title'))}|{query.get('year', '')}"
    return "title:" + hashlib.sha256(key.encode("utf-8", errors="ignore")).hexdigest()[:24]
