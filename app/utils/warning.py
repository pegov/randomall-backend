from typing import List

stopwords_ru = []

stopwords_en = []

profanities_ru = []

profanities_en = []


def get_stopwords(lang: str) -> List[str]:
    if lang == "RU":
        return stopwords_ru
    else:
        return stopwords_en


def get_profanities(lang: str) -> List[str]:
    if lang == "RU":
        return profanities_ru

    else:
        return profanities_en
