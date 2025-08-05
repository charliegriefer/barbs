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
