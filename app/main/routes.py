import json
from typing import Dict, List

import requests
from flask import current_app, render_template, request

from app.extensions import cache
from app.forms import PaginationForm, SearchForm
from app.main import main_blueprint


@main_blueprint.before_request
def load_available_dogs():
    if not cache.has("available_dogs"):
        PETSTABLISHED_BASE_URL = current_app.config['PETSTABLISHED_BASE_URL']
        PETSTABLISHED_PUBLIC_KEY = current_app.config['PETSTABLISHED_PUBLIC_KEY']

        pet_url = f"{PETSTABLISHED_BASE_URL}?public_key={PETSTABLISHED_PUBLIC_KEY}"
        available_dogs = f"{pet_url}&search[status]=Available&sort[order]=asc&sort[column]=name&pagination[limit]=100"

        r = requests.get(available_dogs)
        available_dogs = r.json()
        cache.set("available_dogs", available_dogs, timeout=3600)


@main_blueprint.route("/", methods=["GET", "POST"])
@main_blueprint.route("/index", methods=["GET", "POST"])
def index():
    available_dogs = cache.get("available_dogs").get("collection")
    search_form = SearchForm()
    pagination_form = PaginationForm()

    # create the list of breeds to populate the dropdown
    search_form.breed.choices = [(breed, breed) for breed in get_dog_breeds(available_dogs)]
    search_form.breed.choices.insert(0, ("", "Any"))

    # pagination
    per_page = request.args.get("per_page", 25)
    current_page = request.args.get("current_page", 1)

    # do filtering
    for arg in request.args:
        if request.args.get(arg):
            if arg in ["sex", "age", "size", "shedding"]:
                available_dogs = [dog for dog in available_dogs if dog[arg] == request.args.get(arg)]
                form[arg].process_data(request.args.get(arg))
            if arg in ["is_ok_with_other_dogs", "is_ok_with_other_cats", "is_ok_with_other_kids"]:
                available_dogs = [dog for dog in available_dogs if dog[arg] == "Yes"]
                form[arg].process_data(request.args.get(arg))
            if arg == "breed":
                available_dogs = [dog for dog in available_dogs if request.args.get(arg) in [dog["primary_breed"], dog["secondary_breed"]]]
                form["breed"].process_data(request.args.get("breed"))

    return render_template("index.html",
                           title="Adopt | Puerto Peñasco | Barb's Dog Rescue",
                           pagination_form=pagination_form,
                           search_form=search_form,
                           dogs=available_dogs)


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
