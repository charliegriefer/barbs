import json

import requests
from flask import current_app, render_template, request

from app.extensions import cache
from app.main import main_blueprint


@main_blueprint.before_request
def load_available_dogs():
    if not cache.has("available_dogs"):
        print("GETTING DOGS!!!")
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
    form = SearchForm()

    available_dogs = cache.get("available_dogs").get("collection")
    if request.method == "POST":
        print("----------------------------------")
        print(request.form["age"])
        print("----------------------------------")
        if request.form["gender"] != "":
            available_dogs = [dog for dog in available_dogs if dog["sex"] == request.form["gender"]]
        if request.form["age"] != "":
            available_dogs = [dog for dog in available_dogs if dog["age"] == request.form["age"]]
    return render_template("index.html", title="Home", form=form, dogs=available_dogs)


@main_blueprint.route("/detail/<int:dog_id>")
def dog_detail(dog_id: int):
    available_dogs = cache.get("available_dogs")

    dog = next((item for item in available_dogs.get("collection") if item["id"] == dog_id), None)
    if not dog:
        return render_template("404.html")

    return render_template("detail.html", dog=dog)
