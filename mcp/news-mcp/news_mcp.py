# file: tagesschau_region_mcp_server.py
"""
MCP server fetching Tagesschau news and article details for a given Bundesland (region) and topic (ressort).
Uses Tagesschau public API: https://www.tagesschau.de/api2u/news
"""

from __future__ import annotations
import httpx
import html
import re
from typing import Any, Dict, List
from fastmcp import FastMCP

API_URL = "https://www.tagesschau.de/api2u/news"
USER_AGENT = "tagesschau-mcp/1.0"
MCP_NAME = "tagesschau_news"

mcp = FastMCP(MCP_NAME)


def clean_tagesschau_text(raw_value: str) -> str:
    """Clean Tagesschau API text (escaped HTML → plain text)."""
    if not raw_value:
        return ""
    try:
        decoded = raw_value.encode("utf-8").decode("unicode_escape")
    except Exception:
        decoded = raw_value
    unescaped = html.unescape(decoded)
    return re.sub(r"<[^>]+>", "", unescaped).strip()


@mcp.tool(
    name="fetch_regional_news",
    description=(
        "Fetch Tagesschau news for a given Bundesland (integer region ID 1–16) and topic "
        "(ressort: inland, ausland, wirtschaft, sport, investigativ, video, wissen). "
        "Returns simplified articles with title, date, firstSentence, ressort, and details.\n\n"
        "Bundesland codes:\n"
        "1=Schleswig-Holstein, 2=Hamburg, 3=Niedersachsen, 4=Bremen, 5=Nordrhein-Westfalen, "
        "6=Hessen, 7=Rheinland-Pfalz, 8=Baden-Württemberg, 9=Bayern, 10=Saarland, "
        "11=Berlin, 12=Brandenburg, 13=Mecklenburg-Vorpommern, 14=Sachsen, 15=Sachsen-Anhalt, 16=Thüringen."
    ),
)
async def fetch_regional_news(regions: str, ressort: str) -> List[Dict[str, Any]]:
    """
    Fetch news from Tagesschau API filtered by Bundesland and topic.
    Multiple regions can be comma-separated (e.g. "9,8").
    """
    params = {"regions": regions, "ressort": ressort}
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, params=params, headers=headers, timeout=15.0)
        response.raise_for_status()
        data = response.json()

    if "news" not in data or not isinstance(data["news"], list):
        return []

    simplified = []
    for item in data["news"]:
        simplified.append(
            {
                "title": item.get("title"),
                "date": item.get("date"),
                "firstSentence": clean_tagesschau_text(item.get("firstSentence", "")),
                "ressort": item.get("ressort"),
                "details": item.get("details"),
            }
        )

    return simplified


@mcp.tool(
    name="fetch_default_news_by_ressort",
    description=(
        "Fetch 3 latest Tagesschau news articles per ressort for a given Bundesland (integer region ID 1–16). "
        "Each article includes title, date, firstSentence, ressort, and details."
    ),
)
async def fetch_default_news_by_ressort(region: int) -> Dict[str, List[Dict[str, Any]]]:
    """Fetches 3 articles per ressort for a specific Bundesland."""
    ressorts = ["inland", "ausland", "wirtschaft", "sport", "wissen", "investigativ"]
    results = {}
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        for ressort in ressorts:
            params = {"regions": str(region), "ressort": ressort}
            try:
                resp = await client.get(API_URL, params=params, headers=headers, timeout=15.0)
                resp.raise_for_status()
                data = resp.json()
                articles = data.get("news", [])[:3]
                simplified = [
                    {
                        "title": a.get("title"),
                        "date": a.get("date"),
                        "firstSentence": clean_tagesschau_text(a.get("firstSentence", "")),
                        "details": a.get("details"),
                    }
                    for a in articles
                ]
                results[ressort] = simplified
            except Exception:
                results[ressort] = []
    return results


@mcp.tool(
    name="fetch_article_details",
    description=(
        "Fetch and clean detailed content for a specific Tagesschau article from its 'details' JSON URL. "
        "Only extracts content entries of type 'headline' or 'text' and returns plain text combined as a single paragraph."
    ),
)
async def fetch_article_details(details_url: str) -> Dict[str, Any]:
    """Fetch and clean the article text from a Tagesschau details JSON link."""
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        response = await client.get(details_url, headers=headers, timeout=15.0)
        response.raise_for_status()
        data = response.json()

    content = data.get("content", [])
    text_parts = []
    for block in content:
        if block.get("type") in ("text", "headline"):
            value = block.get("value", "")
            clean_value = clean_tagesschau_text(value)
            if clean_value:
                text_parts.append(clean_value)

    paragraph = "\n\n".join(text_parts)
    return {
        "title": data.get("title"),
        "date": data.get("date"),
        "topline": data.get("topline"),
        "text": paragraph,
    }

# Create ASGI application
# app = mcp.http_app()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
