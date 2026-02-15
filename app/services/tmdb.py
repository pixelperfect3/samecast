import requests
from flask import current_app


class TMDBClient:
    def __init__(self):
        self.api_key = current_app.config["TMDB_API_KEY"]
        self.base_url = current_app.config["TMDB_BASE_URL"]
        self.image_base_url = current_app.config["TMDB_IMAGE_BASE_URL"]

    def _get(self, endpoint, params=None):
        params = params or {}
        params["api_key"] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def search_multi(self, query):
        """Search for movies and TV shows together."""
        data = self._get("search/multi", {"query": query, "include_adult": "false"})
        results = []
        for item in data.get("results", []):
            if item.get("media_type") not in ("movie", "tv"):
                continue
            results.append(self._normalize_search_result(item))
        return results

    def get_movie_details(self, movie_id):
        """Get movie details with credits in one call."""
        data = self._get(f"movie/{movie_id}", {"append_to_response": "credits"})
        return self._normalize_details(data, "movie")

    def get_tv_details(self, tv_id):
        """Get TV show details with aggregate credits (all seasons)."""
        data = self._get(f"tv/{tv_id}", {"append_to_response": "aggregate_credits"})
        return self._normalize_details(data, "tv")

    def get_image_url(self, path, size="w500"):
        """Construct full TMDB image URL."""
        if not path:
            return None
        return f"{self.image_base_url}/{size}{path}"

    def _normalize_search_result(self, item):
        media_type = item.get("media_type", "movie")
        if media_type == "movie":
            title = item.get("title", "")
            date = item.get("release_date", "")
        else:
            title = item.get("name", "")
            date = item.get("first_air_date", "")

        year = int(date[:4]) if date and len(date) >= 4 else None

        return {
            "id": item["id"],
            "media_type": media_type,
            "title": title,
            "release_year": year,
            "overview": item.get("overview", ""),
            "poster_path": item.get("poster_path"),
        }

    def _normalize_details(self, data, media_type):
        if media_type == "movie":
            title = data.get("title", "")
            date = data.get("release_date", "")
            credits_data = data.get("credits", {})
        else:
            title = data.get("name", "")
            date = data.get("first_air_date", "")
            credits_data = data.get("aggregate_credits", {})

        year = int(date[:4]) if date and len(date) >= 4 else None

        cast = []
        for member in credits_data.get("cast", []):
            entry = {
                "person_id": member["id"],
                "name": member.get("name", ""),
                "profile_path": member.get("profile_path"),
                "known_for_department": member.get("known_for_department"),
                "credit_type": "cast",
                "display_order": member.get("order", 999),
            }
            # TV aggregate_credits nests roles differently
            if media_type == "tv":
                roles = member.get("roles", [])
                characters = [r.get("character", "") for r in roles if r.get("character")]
                entry["character"] = " / ".join(characters) if characters else ""
            else:
                entry["character"] = member.get("character", "")
            cast.append(entry)

        crew = []
        for member in credits_data.get("crew", []):
            entry = {
                "person_id": member["id"],
                "name": member.get("name", ""),
                "profile_path": member.get("profile_path"),
                "known_for_department": member.get("known_for_department"),
                "credit_type": "crew",
            }
            if media_type == "tv":
                jobs = member.get("jobs", [])
                job_names = [j.get("job", "") for j in jobs if j.get("job")]
                entry["job"] = " / ".join(job_names) if job_names else ""
                entry["department"] = member.get("department", "")
            else:
                entry["job"] = member.get("job", "")
                entry["department"] = member.get("department", "")
            crew.append(entry)

        return {
            "id": data["id"],
            "media_type": media_type,
            "title": title,
            "release_year": year,
            "overview": data.get("overview", ""),
            "poster_path": data.get("poster_path"),
            "cast": cast,
            "crew": crew,
        }
