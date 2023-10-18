from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Depends, Response

from app.config import LANGUAGE
from app.repo.gens import GensRepo
from app.routers.dependencies import get_gens_repo

router = APIRouter()

"""
/sitemap.xml
"""


@router.get("/sitemap.xml", name="sitemap")
async def get_sitemap(gens_repo: GensRepo = Depends(get_gens_repo)):
    if LANGUAGE == "RU":
        gens = await gens_repo.get_sitemap()
        main = [
            {"loc": "https://randomall.ru", "changefreq": "weekly", "priority": "1.0"},
        ]
        creative_urls = [
            "fantasy_name",
            "appearance",
            "crowd",
            "character",
            "motivation",
            "abilities",
            "features",
            "jobs",
            "race",
            "superpowers",
            "plot",
            "plotkeys",
            "awkward_moment",
            "unexpected_event",
            "bookname",
            "fantasy_continent",
            "fantasy_country",
            "fantasy_town",
            "country_description",
        ]
        creative = [
            {
                "loc": f"https://randomall.ru/{url}",
                "changefreq": "weekly",
                "priority": "0.9",
            }
            for url in creative_urls
        ]
        general_urls = [
            "numbers",
            "names",
            "surnames",
            "date",
            "time",
            "countries",
            "cities",
            "cubes",
            "coin",
        ]
        general = [
            {
                "loc": f"https://randomall.ru/{url}",
                "changefreq": "weekly",
                "priority": "0.7",
            }
            for url in general_urls
        ]
        custom = [
            {
                "loc": f"https://randomall.ru/custom/gen/{gen.get('id')}",
                "lastmod": gen.get("date_updated").strftime("%Y-%m-%d"),
                "changefreq": "weekly",
                "priority": "0.9",
            }
            for gen in gens
        ]
        urlset = Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        for category in [main, creative, general, custom]:
            for obj in category:
                url = SubElement(urlset, "url")
                for key, value in obj.items():
                    el = SubElement(url, key)
                    el.text = value

        data = """<?xml version="1.0" encoding="UTF-8"?>
        """
        data += tostring(urlset, encoding="unicode")
        return Response(content=data, media_type="application/xml")
    else:
        main = [
            {
                "loc": "https://creativeton.com",
                "changefreq": "weekly",
                "priority": "1.0",
            },
        ]
        gens = await gens_repo.get_sitemap()
        custom = [
            {
                "loc": f"https://creativeton.com/gens/{gen.get('id')}",
                "lastmod": gen.get("date_updated").strftime("%Y-%m-%d"),
                "changefreq": "weekly",
                "priority": "0.9",
            }
            for gen in gens
        ]
        urlset = Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        for obj in custom:
            url = SubElement(urlset, "url")
            for key, value in obj.items():
                el = SubElement(url, key)
                el.text = value
        data = """<?xml version="1.0" encoding="UTF-8"?>
        """
        data += tostring(urlset, encoding="unicode")
        return Response(content=data, media_type="application/xml")
