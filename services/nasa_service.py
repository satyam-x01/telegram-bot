import os
import requests
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config

class NASAService:
    def __init__(self):
        self.api_key = config.NASA_API_KEY or "80hAffCZFhiKukatz44X4iJ15mkdQvgfut50qWGd"
        self.base_url = "https://api.nasa.gov"
        self.images_api_url = "https://images-api.nasa.gov"
        self._cache = {}
        self._cache_time = {}

    def _is_cache_valid(self, key: str, ttl_seconds: int = 1800) -> bool:
        if key in self._cache and key in self._cache_time:
            return (datetime.now().timestamp() - self._cache_time[key]) < ttl_seconds
        return False

    def get_apod(self, date: Optional[str] = None) -> Optional[Dict]:
        """Fetch Astronomy Picture of the Day from NASA API."""
        cache_key = f"apod_{date or 'today'}"
        if self._is_cache_valid(cache_key, ttl_seconds=1800):
            return self._cache[cache_key]

        try:
            url = f"{self.base_url}/planetary/apod"
            params = {"api_key": self.api_key}
            if date:
                params["date"] = date
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                result = {
                    "title": data.get("title", "Astronomy Picture of the Day"),
                    "explanation": data.get("explanation", ""),
                    "url": data.get("url", ""),
                    "hdurl": data.get("hdurl", data.get("url", "")),
                    "media_type": data.get("media_type", "image"),
                    "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "copyright": data.get("copyright", "NASA / Public Domain")
                }
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now().timestamp()
                return result
        except Exception as e:
            print(f"Error fetching APOD: {e}")

        # Robust Fallback: fetch from newest James Webb or Deep Space photos from NASA Images API
        fallback_photos = self.get_latest_astronomy_photos("James Webb", limit=5)
        if fallback_photos:
            item = fallback_photos[0]
            return {
                "title": item["title"],
                "explanation": item["description"],
                "url": item["img_url"],
                "hdurl": item["img_url"],
                "media_type": "image",
                "date": item["date"] or datetime.now().strftime("%Y-%m-%d"),
                "copyright": "NASA / James Webb Space Telescope"
            }
        return None

    def get_recent_apods(self, limit: int = 15) -> List[Dict]:
        """Fetch latest Astronomy Pictures of the Day from recent days (newest first)."""
        cache_key = f"recent_apods_{limit}"
        if self._is_cache_valid(cache_key, ttl_seconds=1800):
            return self._cache[cache_key]

        try:
            start_date = (datetime.now() - timedelta(days=limit + 5)).strftime("%Y-%m-%d")
            url = f"{self.base_url}/planetary/apod"
            params = {
                "api_key": self.api_key,
                "start_date": start_date
            }
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    # Filter only image APODs and sort in reverse chronological order (newest first)
                    image_items = [item for item in data if item.get("media_type") == "image"]
                    image_items.reverse()
                    results = []
                    for item in image_items[:limit]:
                        results.append({
                            "title": item.get("title", "Astronomy Picture of the Day"),
                            "explanation": item.get("explanation", ""),
                            "url": item.get("url", ""),
                            "hdurl": item.get("hdurl", item.get("url", "")),
                            "media_type": "image",
                            "date": item.get("date", ""),
                            "copyright": item.get("copyright", "NASA / Public Domain")
                        })
                    if results:
                        self._cache[cache_key] = results
                        self._cache_time[cache_key] = datetime.now().timestamp()
                        return results
        except Exception as e:
            print(f"Error fetching recent APODs: {e}")
        return []

    def get_latest_astronomy_photos(self, query: str = "James Webb Space Telescope", limit: int = 20) -> List[Dict]:
        """Fetch newest astronomy photos from NASA Image Library (JWST, Hubble, Deep Space)."""
        cache_key = f"latest_astro_{query}_{limit}"
        if self._is_cache_valid(cache_key, ttl_seconds=3600):
            return self._cache[cache_key]

        try:
            url = f"{self.images_api_url}/search"
            # Search recent years first for modern high-resolution photos
            for year_start in ["2024", "2023", ""]:
                params = {"q": query, "media_type": "image"}
                if year_start:
                    params["year_start"] = year_start

                resp = requests.get(url, params=params, timeout=12)
                if resp.status_code == 200:
                    items = resp.json().get("collection", {}).get("items", [])
                    results = []
                    skip_keywords = [
                        "screening", "briefing", "conference", "portrait", "ceremony", 
                        "meeting", "awards", "panel", "auditorium", "announcement", "headquarters", "hq"
                    ]
                    for item in items:
                        data_list = item.get("data", [{}])
                        links_list = item.get("links", [{}])
                        if data_list and links_list:
                            data = data_list[0]
                            title = data.get("title", "NASA Astronomy Photo")
                            if any(k in title.lower() for k in skip_keywords):
                                continue

                            img_url = links_list[0].get("href", "")
                            if img_url:
                                high_res_url = img_url.replace("~thumb.", "~large.")
                                results.append({
                                    "title": title,
                                    "description": data.get("description", "Latest deep space observation from NASA."),
                                    "img_url": high_res_url,
                                    "date": data.get("date_created", "")[:10],
                                    "nasa_id": data.get("nasa_id", ""),
                                    "source": "NASA James Webb / Hubble Telescopes"
                                })
                                if len(results) >= limit:
                                    break
                    if results:
                        self._cache[cache_key] = results
                        self._cache_time[cache_key] = datetime.now().timestamp()
                        return results
        except Exception as e:
            print(f"Error fetching latest astronomy photos: {e}")
        return []

    def get_asteroids(self, date_str: Optional[str] = None) -> Optional[Dict]:
        """Fetch Near-Earth Objects (Asteroids) for today."""
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            url = f"{self.base_url}/neo/rest/v1/feed"
            params = {
                "start_date": date_str,
                "end_date": date_str,
                "api_key": self.api_key
            }
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                element_count = data.get("element_count", 0)
                near_earth_objects = data.get("near_earth_objects", {}).get(date_str, [])
                asteroids = []
                for item in near_earth_objects[:5]: # top 5
                    name = item.get("name", "Unknown Asteroid")
                    hazardous = item.get("is_potentially_hazardous_asteroid", False)
                    diameter_max = item.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0)
                    close_data = item.get("close_approach_data", [{}])[0]
                    miss_distance_km = float(close_data.get("miss_distance", {}).get("kilometers", 0))
                    velocity_kph = float(close_data.get("relative_velocity", {}).get("kilometers_per_hour", 0))
                    
                    asteroids.append({
                        "name": name,
                        "hazardous": hazardous,
                        "diameter_m": round(diameter_max, 1),
                        "miss_distance_km": f"{miss_distance_km:,.0f}",
                        "velocity_kph": f"{velocity_kph:,.0f}"
                    })
                return {
                    "date": date_str,
                    "total_count": element_count,
                    "asteroids": asteroids
                }
        except Exception as e:
            print(f"Error fetching Asteroids: {e}")
        return None

    def get_mars_photos(self) -> Optional[Dict]:
        """Fetch latest Perseverance or Curiosity Mars Rover photo directly from NASA Images API."""
        cache_key = "mars_latest_photos"
        if self._is_cache_valid(cache_key, ttl_seconds=3600):
            cached = self._cache[cache_key]
            if cached:
                return random.choice(cached)

        try:
            url = f"{self.images_api_url}/search"
            params = {
                "q": "Perseverance Mars Rover surface",
                "media_type": "image",
                "year_start": "2024"
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("collection", {}).get("items", [])
                candidates = []
                skip_keywords = ["briefing", "conference", "portrait", "screening", "ceremony", "auditorium"]
                for item in items:
                    data = item.get("data", [{}])[0]
                    title = data.get("title", "")
                    if any(k in title.lower() for k in skip_keywords):
                        continue
                    links = item.get("links", [{}])
                    img_url = links[0].get("href", "") if links else ""
                    if img_url:
                        candidates.append({
                            "rover": "Perseverance",
                            "img_url": img_url.replace("~thumb.", "~large."),
                            "earth_date": data.get("date_created", "")[:10],
                            "camera_full_name": title,
                            "status": "active",
                            "total_photos": 100000
                        })
                if candidates:
                    self._cache[cache_key] = candidates
                    self._cache_time[cache_key] = datetime.now().timestamp()
                    return random.choice(candidates)
        except Exception as e:
            print(f"Error fetching latest Mars photo: {e}")

        # Fallback to general Mars surface images
        fallback_images = self.get_nasa_images("Mars rover surface panorama")
        if fallback_images:
            item = random.choice(fallback_images)
            return {
                "rover": "Curiosity / Perseverance",
                "img_url": item["img_url"],
                "earth_date": datetime.now().strftime("%Y-%m-%d"),
                "camera_full_name": item["title"],
                "status": "active",
                "total_photos": 100000
            }
        return None

    def get_nasa_images(self, query: str, year_start: Optional[str] = None) -> List[Dict]:
        """Search NASA's public image gallery with optional recency filter."""
        try:
            url = f"{self.images_api_url}/search"
            params = {"q": query, "media_type": "image"}
            if year_start:
                params["year_start"] = year_start
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                items = resp.json().get("collection", {}).get("items", [])
                results = []
                for item in items[:6]:
                    data_list = item.get("data", [{}])
                    links_list = item.get("links", [{}])
                    if data_list and links_list:
                        title = data_list[0].get("title", "NASA Image")
                        desc = data_list[0].get("description", "No description available.")
                        img_url = links_list[0].get("href", "")
                        if img_url:
                            high_res = img_url.replace("~thumb.", "~large.")
                            results.append({
                                "title": title,
                                "description": desc[:300] + "..." if len(desc) > 300 else desc,
                                "img_url": high_res
                            })
                return results
        except Exception as e:
            print(f"Error searching NASA images: {e}")
        return []

    def get_exoplanet_catalog(self) -> List[Dict]:
        """Curated NASA Exoplanets list with scientific details for interactive discovery."""
        return [
            {
                "name": "TOI-700 d",
                "distance": "101.4 light years",
                "type": "Super-Earth / Earth-size Habitable Zone Planet",
                "star": "TOI-700 (M-dwarf)",
                "discovered": "2020 by NASA TESS Mission",
                "fact": "TOI-700 d is one of the few Earth-sized planets discovered in a star's habitable zone where liquid water could exist on its surface!",
                "image": "https://images-assets.nasa.gov/image/PIA23408/PIA23408~orig.jpg"
            },
            {
                "name": "Kepler-1649c",
                "distance": "300 light years",
                "type": "Earth-sized Exoplanet",
                "star": "Kepler-1649 (Red Dwarf)",
                "discovered": "2020 by NASA Kepler Telescope Data",
                "fact": "Kepler-1649c is 1.06 times the size of Earth and receives 75% of the light Earth gets from the Sun, making its temperature similar to Earth!",
                "image": "https://images-assets.nasa.gov/image/PIA23648/PIA23648~orig.jpg"
            },
            {
                "name": "LHS 475 b",
                "distance": "41 light years",
                "type": "Rocky Terrestrial Planet",
                "star": "LHS 475 (Red Dwarf)",
                "discovered": "2023 by NASA James Webb Space Telescope (JWST)",
                "fact": "LHS 475 b was the FIRST exoplanet confirmed using the James Webb Space Telescope! It is almost identical in diameter to Earth (99% Earth size).",
                "image": "https://images-assets.nasa.gov/image/PIA25673/PIA25673~orig.jpg"
            },
            {
                "name": "K2-18 b",
                "distance": "120 light years",
                "type": "Hycean Sub-Neptune Planet",
                "star": "K2-18 (Red Dwarf)",
                "discovered": "2015 by NASA Kepler, detailed by JWST in 2023",
                "fact": "JWST detected carbon-bearing molecules (CO2 and methane) in K2-18 b's atmosphere, suggesting it might be a Hycean planet with a global water ocean and hydrogen atmosphere!",
                "image": "https://images-assets.nasa.gov/image/PIA25964/PIA25964~orig.jpg"
            },
            {
                "name": "HD 110067 system",
                "distance": "100 light years",
                "type": "Sub-Neptune 6-Planet Resonant System",
                "star": "HD 110067 (Orange Star)",
                "discovered": "2023 by NASA TESS and ESA CHEOPS",
                "fact": "HD 110067 is a rare star system with SIX sub-Neptune planets locked in a perfect rhythmic orbital harmony (resonance) that has been undisturbed for over a billion years!",
                "image": "https://images-assets.nasa.gov/image/PIA26154/PIA26154~orig.jpg"
            }
        ]

nasa_service = NASAService()
