import math
from typing import Dict, List, Tuple

import requests
from flask import current_app


class DogService:
    """Handles all dog-related business logic"""

    def __init__(self, cache):
        self.cache = cache

    def load_available_dogs(self) -> None:
        """Load available dogs from API and cache them"""
        if not self.cache.has("available_dogs"):
            base_url = current_app.config["PETSTABLISHED_BASE_URL"]
            public_key = current_app.config["PETSTABLISHED_PUBLIC_KEY"]

            pet_url = f"{base_url}?public_key={public_key}"
            pet_url += "&search[status]=Available&sort[order]=asc&sort[column]=name&pagination[limit]=100"

            available_dogs = []
            current_page = 1

            while True:
                tmp_url = f"{pet_url}&pagination[page]={current_page}"
                api_dogs = requests.get(tmp_url)
                dogs = api_dogs.json()

                # filter out any non-Available dogs (see: issue #32)
                available_dogs.extend(
                    [d for d in dogs["collection"] if d.get("status") == "Available"]
                )

                if len(dogs["collection"]) == 100:
                    current_page += 1
                else:
                    break

            self.cache.set("available_dogs", available_dogs, timeout=3600)

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
