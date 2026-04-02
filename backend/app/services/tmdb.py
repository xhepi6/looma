import logging

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"


async def fetch_tmdb_metadata(title: str, media_type: str) -> dict | None:
    """Fetch metadata from TMDB for a movie or TV show.

    Returns a dict with keys: year, genre, rating, synopsis, seasons, tmdb_id
    or None on any failure. Never raises.
    """
    if not title or not title.strip():
        return None

    if not settings.tmdb_api_key or not settings.tmdb_enabled:
        return None

    search_type = "movie" if media_type == "movie" else "tv"

    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.tmdb_api_key}",
                "Accept": "application/json",
            }

            # Search by title
            search_resp = await client.get(
                f"{TMDB_BASE_URL}/search/{search_type}",
                params={"query": title, "language": "en-US", "page": 1},
                headers=headers,
                timeout=15.0,
            )
            search_resp.raise_for_status()
            results = search_resp.json().get("results", [])

            if not results:
                logger.info("TMDB: no results for '%s' (%s)", title[:80], search_type)
                return None

            tmdb_id = results[0]["id"]

            # Get full details
            detail_resp = await client.get(
                f"{TMDB_BASE_URL}/{search_type}/{tmdb_id}",
                params={"language": "en-US"},
                headers=headers,
                timeout=15.0,
            )
            detail_resp.raise_for_status()
            detail = detail_resp.json()

            # Extract year
            date_field = "release_date" if search_type == "movie" else "first_air_date"
            date_str = detail.get(date_field, "")
            year = int(date_str[:4]) if date_str and len(date_str) >= 4 else None

            genres = ", ".join(g["name"] for g in detail.get("genres", []))
            rating = detail.get("vote_average")
            synopsis = detail.get("overview")
            seasons = detail.get("number_of_seasons") if search_type == "tv" else None

            return {
                "tmdb_id": tmdb_id,
                "year": year,
                "genre": genres or None,
                "rating": round(rating, 1) if rating else None,
                "synopsis": synopsis or None,
                "seasons": seasons,
            }
    except Exception:
        logger.warning("TMDB fetch failed for '%s'", title[:80], exc_info=True)
        return None
