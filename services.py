import math
import time
from typing import Dict, List, Tuple

import requests
from flask import current_app


class DogService:
    """Handles all dog-related business logic"""

    def __init__(self, cache):
        self.cache = cache

    def load_available_dogs(self) -> None:
        """Load available dogs from API and cache them (Redis-safe across Gunicorn workers)."""

        # Fast path: already cached
        cached = self.cache.get("available_dogs")
        if cached is not None:
            return

        lock_key = "available_dogs_lock"

        # Try to become the one worker that populates the cache
        got_lock = self._acquire_lock(lock_key, ttl_seconds=45)

        if not got_lock:
            # Another worker is fetching. Wait briefly for cache to appear.
            # (This avoids hammering the API and avoids caching partial results.)
            for _ in range(30):  # ~3 seconds total
                time.sleep(0.1)
                cached = self.cache.get("available_dogs")
                if cached is not None:
                    return

            # If cache still isn't ready, fall through and fetch anyway (rare).
            # This is a fail-open so the page still works.
            # You could also just `return` here if you prefer.
            got_lock = True

        try:
            # Double-check after acquiring lock (another worker may have populated it)
            cached = self.cache.get("available_dogs")
            if cached is not None:
                return

            base_url = current_app.config["PETSTABLISHED_BASE_URL"]
            public_key = current_app.config["PETSTABLISHED_PUBLIC_KEY"]

            pet_url = f"{base_url}?public_key={public_key}"
            pet_url += "&search[status]=Available&sort[order]=asc&sort[column]=name&pagination[limit]=100"

            available_dogs = []
            current_page = 1

            while True:

                tmp_url = f"{pet_url}&pagination[page]={current_page}"
                api_dogs = requests.get(tmp_url, timeout=15)
                api_dogs.raise_for_status()
                dogs = api_dogs.json()
                tail = [
                    (
                        d.get("name"),
                        d.get("id"),
                        d.get("status"),
                        d.get("bonded"),
                        d.get("bonded_group_id"),
                    )
                    for d in dogs["collection"][-10:]
                ]
                current_app.logger.warning("PAGE %s tail=%s", current_page, tail)

                import json

                with open("page1.json", "w") as f:
                    json.dump(dogs, f, indent=2)

                # filter out any non-Available dogs (see: issue #32)
                available_dogs.extend(
                    [d for d in dogs["collection"] if d.get("status") == "Available"]
                )
                current_app.logger.warning(
                    "Petstablished page %s returned %s dogs",
                    current_page,
                    len(dogs["collection"]),
                )
                pagination = dogs.get("pagination") or {}
                total_pages = int(pagination.get("total_pages", current_page))

                if current_page < total_pages:
                    current_page += 1
                else:
                    break

            # De-dupe dogs by ID (Petstablished can return duplicates, e.g. bonded pairs)
            deduped = {}
            for d in available_dogs:
                dog_id = d.get("id")
                if dog_id is not None:
                    deduped[dog_id] = d

            available_dogs = list(deduped.values())

            self.cache.set("available_dogs", available_dogs, timeout=3600)

        finally:
            if got_lock:
                self._release_lock(lock_key)

    def get_available_dogs(self) -> List[Dict]:
        """Get cached available dogs"""
        return self.cache.get("available_dogs") or []

    def get_dog_by_id(self, dog_id: int) -> Dict:
        """Find a specific dog by ID"""
        available_dogs = self.get_available_dogs()
        return next((item for item in available_dogs if item["id"] == dog_id), None)

    def get_dog_breeds(self, dogs: List[Dict]) -> List[str]:
        """Extract and return sorted list of unique breeds"""
        breeds = set()

        for dog in dogs:
            if dog.get("primary_breed"):
                breeds.add(dog.get("primary_breed"))
            if dog.get("secondary_breed"):
                breeds.add(dog.get("secondary_breed"))

        return sorted(list(breeds))

    def filter_dogs(self, dogs: List[Dict], filters: Dict) -> List[Dict]:
        """Apply search filters to dog list"""
        filtered_dogs = dogs.copy()

        for key, value in filters.items():
            if not value:
                continue

            if key in ["sex", "age", "size", "shedding"]:
                filtered_dogs = [dog for dog in filtered_dogs if dog.get(key) == value]
            elif key == "breed":
                filtered_dogs = [
                    dog
                    for dog in filtered_dogs
                    if value in [dog.get("primary_breed"), dog.get("secondary_breed")]
                ]

        return filtered_dogs

    def paginate_dogs(
        self, dogs: List[Dict], page: int, per_page: int
    ) -> Tuple[List[Dict], int]:
        """Paginate dog list and return dogs + total pages"""
        total_dogs = len(dogs)

        if per_page == 999:  # Show all
            return dogs, 1

        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_dogs = dogs[start_index:end_index]
        total_pages = math.ceil(total_dogs / per_page)

        return paginated_dogs, total_pages

    def extract_filters(self, request_args: Dict) -> Dict:
        """Extract valid filters from request arguments"""
        return {
            key: value
            for key, value in request_args.items()
            if key in ["sex", "age", "size", "shedding", "breed"] and value
        }

    def get_pagination_settings(
        self, request_args: Dict, total_dogs: int
    ) -> Tuple[int, int]:
        """Extract and validate pagination settings"""
        per_page = int(request_args.get("per_page", 24))
        if request_args.get("per_page") == "999":
            per_page = total_dogs

        current_page = int(request_args.get("current_page", 1))
        return per_page, current_page

    def process_search_request(self, request_args: Dict) -> Dict:
        """Process a complete search request with filtering and pagination"""
        # Get all dogs
        available_dogs = self.get_available_dogs()

        # Extract filters and apply them
        filters = self.extract_filters(request_args)
        filtered_dogs = self.filter_dogs(available_dogs, filters)
        total_dogs = len(filtered_dogs)

        # Handle pagination
        per_page, current_page = self.get_pagination_settings(
            request_args, len(available_dogs)
        )
        paginated_dogs, number_of_pages = self.paginate_dogs(
            filtered_dogs, current_page, per_page
        )

        # Get breeds for form choices
        breeds = self.get_dog_breeds(available_dogs)

        return {
            "dogs": paginated_dogs,
            "total_dogs": total_dogs,
            "current_page": current_page,
            "per_page": per_page,
            "number_of_pages": number_of_pages,
            "breeds": breeds,
            "filters": filters,
        }

    def prepare_forms(self, search_data: Dict):
        """Prepare and configure forms with current data"""
        from forms import PaginationForm, SearchForm

        # Initialize forms
        search_form = SearchForm()
        pagination_form = PaginationForm()

        # Populate breed choices
        search_form.breed.choices = [("", "Any")] + [
            (breed, breed) for breed in search_data["breeds"]
        ]

        # Set form values from filters
        for key, value in search_data["filters"].items():
            if hasattr(search_form, key):
                getattr(search_form, key).process_data(value)

        # Set pagination form value (convert back to 999 for "All" option)
        pagination_value = (
            999
            if search_data["per_page"] == len(self.get_available_dogs())
            else search_data["per_page"]
        )
        pagination_form.per_page.process_data(pagination_value)

        return search_form, pagination_form

    def _acquire_lock(self, lock_key: str, ttl_seconds: int = 30) -> bool:
        """
        Acquire a Redis lock using SET NX EX.
        Works when CACHE_TYPE is RedisCache and self.cache.cache is a redis.Redis client.
        Returns True if lock acquired, False otherwise.
        """
        redis_client = getattr(self.cache, "cache", None)
        if redis_client is None:
            # Not Redis-backed (or cannot access client)
            return True

        try:
            # SET lock_key "1" NX EX ttl_seconds
            return bool(redis_client.set(lock_key, "1", nx=True, ex=ttl_seconds))
        except Exception:
            # If Redis hiccups, fail open rather than break the site
            return True

    def _release_lock(self, lock_key: str) -> None:
        redis_client = getattr(self.cache, "cache", None)
        if redis_client is None:
            return
        try:
            redis_client.delete(lock_key)
        except Exception:
            pass
