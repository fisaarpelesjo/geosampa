import re
import unicodedata


def keyword_in_text(keyword: str, text: str) -> bool:
    normalized_keyword = normalize_text(keyword)
    if not normalized_keyword:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_keyword)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s:.-]", " ", ascii_text.lower())).strip()


def match_keywords(text: str, keywords: list[str]) -> list[str]:
    normalized_text = normalize_text(text)
    matches: list[str] = []
    for keyword in keywords:
        if keyword_in_text(keyword, normalized_text):
            matches.append(keyword)
    return sorted(set(matches), key=matches.index)

