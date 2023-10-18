def validate_usergen(s: str) -> bool:
    stop_words = [
        "<script",
        "+79",
    ]

    for word in stop_words:
        if word in s:
            return False

    return True
