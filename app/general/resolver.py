from typing import Optional

from app.general.generators import (
    get_abilities,
    get_appearance,
    get_awkward_moment,
    get_bookname,
    get_character,
    get_cities,
    get_continent,
    get_countries,
    get_country_description,
    get_crowd,
    get_date,
    get_fantasy_country,
    get_fantasy_name,
    get_fantasy_town,
    get_features,
    get_jobs,
    get_motivation,
    get_names,
    get_numbers,
    get_plot,
    get_plot_keys,
    get_race,
    get_superpowers,
    get_surnames,
    get_time,
    get_unexpected_event,
)
from app.repo.general import GeneralRepo


async def resolve_generation(repo: GeneralRepo, name: str, data: Optional[dict] = None):
    nothing = {
        "country_description": get_country_description,
        "fantasy_country": get_fantasy_country,
        "fantasy_town": get_fantasy_town,
        "fantasy_continent": get_continent,
        "fantasy_name": get_fantasy_name,
        "abilities": get_abilities,
    }
    with_repo = {
        "cities": get_cities,
        "countries": get_countries,
        "jobs": get_jobs,
        "superpowers": get_superpowers,
        "character": get_character,
        "race": get_race,
        "motivation": get_motivation,
        "features": get_features,
        "crowd": get_crowd,
        "awkward_moment": get_awkward_moment,
        "unexpected_event": get_unexpected_event,
        "bookname": get_bookname,
        "plot": get_plot,
        "surnames": get_surnames,
    }
    with_data = {
        "plotkeys": get_plot_keys,
        "appearance": get_appearance,
        "numbers": get_numbers,
        "time": get_time,
        "date": get_date,
    }
    both = {
        "names": get_names,
    }

    if name in with_data:
        return with_data[name](data)

    if name in with_repo:
        return await with_repo[name](repo)

    if name in nothing:
        return nothing[name]()

    if name in both:
        return await both[name](repo, data)

    return None
