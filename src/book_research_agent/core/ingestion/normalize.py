def normalize_text(text: str) -> str:
    normalized = text.removeprefix("\ufeff")
    normalized = normalized.replace("\r\n", "\n")
    normalized = normalized.replace("\r", "\n")
    return normalized
