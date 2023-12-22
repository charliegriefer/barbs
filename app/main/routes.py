import json

import requests
from flask import current_app, render_template, request

from app.extensions import cache
from app.forms import SearchForm
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
    form = SearchForm()

    # create the list of breeds to populate the dropdown
    breeds = set()
    [breeds.add(breed.get("primary_breed")) for breed in available_dogs if breed.get("primary_breed") != ""]
    [breeds.add(breed.get("secondary_breed")) for breed in available_dogs if breed.get("secondary_breed") != ""]

    form_breeds = list(breeds)
    form_breeds.sort()

    form.breed.choices = [(breed, breed) for breed in form_breeds]
    form.breed.choices.insert(0, ("", "Any"))

    if request.method == "POST":
        if request.form["gender"] != "":
            available_dogs = [dog for dog in available_dogs if dog["sex"] == request.form["gender"]]
        if request.form["age"] != "":
            available_dogs = [dog for dog in available_dogs if dog["age"] == request.form["age"]]
        if request.form["breed"] != "":
            available_dogs = [dog for dog in available_dogs
                if dog["primary_breed"] == request.form["breed"] or dog["secondary_breed"] == request.form["breed"]]
        if request.form["shedding"] != "":
            available_dogs = [dog for dog in available_dogs if dog["shedding"] == request.form["shedding"]]
        if request.form["size"] != "":
            available_dogs = [dog for dog in available_dogs if dog["size"] == request.form["size"]]
        if request.form.get("is_ok_with_other_dogs"):
            available_dogs = [dog for dog in available_dogs if dog["is_ok_with_other_dogs"] == "Yes"]
        if request.form.get("is_ok_with_other_cats"):
            available_dogs = [dog for dog in available_dogs if dog["is_ok_with_other_cats"] == "Yes"]
        if request.form.get("is_ok_with_other_kids"):
            available_dogs = [dog for dog in available_dogs if dog["is_ok_with_other_kids"] == "Yes"]

    return render_template("index.html", title="Home", form=form, dogs=available_dogs)


@main_blueprint.route("/detail/<int:dog_id>")
def dog_detail(dog_id: int):
    available_dogs = cache.get("available_dogs")

    dog = next((item for item in available_dogs.get("collection") if item["id"] == dog_id), None)
    if not dog:
        return render_template("404.html")

    return render_template("detail.html", dog=dog)
