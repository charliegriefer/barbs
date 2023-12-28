import json
import math
from typing import Dict, List

import requests
from flask import current_app, flash, render_template, request

from app.extensions import cache
from app.forms import PaginationForm, SearchForm
from app.main import main_blueprint


@main_blueprint.before_request
def load_available_dogs():
    if not cache.has("available_dogs"):
        flash("DEBUGGING: No cache. Hitting API.")
        PETSTABLISHED_BASE_URL = current_app.config['PETSTABLISHED_BASE_URL']
        PETSTABLISHED_PUBLIC_KEY = current_app.config['PETSTABLISHED_PUBLIC_KEY']

        pet_url = f"{PETSTABLISHED_BASE_URL}?public_key={PETSTABLISHED_PUBLIC_KEY}"
        available_dogs = f"{pet_url}&search[status]=Available&sort[order]=asc&sort[column]=name&pagination[limit]=100"

        r = requests.get(available_dogs)
        available_dogs = r.json()
        cache.set("available_dogs", available_dogs, timeout=3600)
    else:
        flash("DEBUGGING: Cached data. No API call needed.")

@main_blueprint.route("/")
@main_blueprint.route("/index")
def index():
    available_dogs = cache.get("available_dogs").get("collection")
    search_form = SearchForm()
    pagination_form = PaginationForm()

    # create the list of breeds to populate the dropdown
    search_form.breed.choices = [(breed, breed) for breed in get_dog_breeds(available_dogs)]
    search_form.breed.choices.insert(0, ("", "Any"))

    # pagination
    per_page = int(request.args.get("per_page", 25))
    current_page = request.args.get("current_page", 1)
    pagination_form["per_page"].process_data(per_page)

    # do filtering
    for key, value in request.args.items():
        if key in ["sex", "age", "size", "shedding", "breed"] and value:
            if key in ["sex", "age", "size", "shedding"]:
                available_dogs = [dog for dog in available_dogs if dog[key] == value]
            if key == "breed":
                breeds = [dog["primary_breed"], dog["secondary_breed"]]
                available_dogs = [dog for dog in available_dogs if value in breeds]
            search_form[key].process_data(value)

    available_dogs_total = len(available_dogs)

    # TODO: make "is_embedded" a url param. will have to change line 48 above to skip it.
    is_embedded = False
    if request.path == "/index_embedded":
        is_embedded = True

    # pagination
    view_start = (int(current_page) - 1) * per_page
    available_dogs = available_dogs[view_start:view_start + per_page]
    number_of_pages = math.ceil(available_dogs_total/per_page)

    print("per_page: ", per_page)
    print("view_start: ", view_start)
    print("number_of_pages: ", number_of_pages)
    print("current_page: ", current_page)

    # for pagination links
    qs = []
    for key, value in request.args.items():
        qs.append(f"{key}={value}")

    return render_template("index.html",
                           title="Adopt | Puerto Peñasco | Barb's Dog Rescue",
                           pagination_form=pagination_form,
                           search_form=search_form,
                           dogs=available_dogs,
                           available_dogs_total=available_dogs_total,
                           is_embedded=is_embedded,
                           current_page=int(current_page),
                           per_page=int(per_page),
                           number_of_pages=int(number_of_pages),
                           qs="&".join(qs))


@main_blueprint.route("/detail/<int:dog_id>")
def dog_detail(dog_id: int):
    available_dogs = cache.get("available_dogs")

    dog = next((item for item in available_dogs.get("collection") if item["id"] == dog_id), None)
    if not dog:
        return render_template("404.html")

    return render_template("detail.html", dog=dog)


def get_dog_breeds(available_dogs: List[Dict[str, str]]) -> List[str]:
    """
    Given a list of available dogs, return a list of distinct breeds
    """
    breeds = set()
    [breeds.add(breed.get("primary_breed")) for breed in available_dogs if breed.get("primary_breed") != ""]
    [breeds.add(breed.get("secondary_breed")) for breed in available_dogs if breed.get("secondary_breed") != ""]

    form_breeds = list(breeds)
    form_breeds.sort()
    return form_breeds
