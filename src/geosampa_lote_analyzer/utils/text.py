import re
import unicodedata


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
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword and normalized_keyword in normalized_text:
            matches.append(keyword)
    return sorted(set(matches), key=matches.index)

