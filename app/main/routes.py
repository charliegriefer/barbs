import json

import requests
from flask import current_app, render_template

from app.extensions import cache
from app.main import main_blueprint

@main_blueprint.route("/")
@main_blueprint.route("/index")
def index():
    PETSTABLISHED_BASE_URL = current_app.config['PETSTABLISHED_BASE_URL']
    PETSTABLISHED_PUBLIC_KEY = current_app.config['PETSTABLISHED_PUBLIC_KEY']

    pet_url = f"{PETSTABLISHED_BASE_URL}?public_key={PETSTABLISHED_PUBLIC_KEY}"

    available_dogs_url = f"{pet_url}&search[status]=Available&sort[order]=asc&sort[column]=name&pagination[limit]=100"

    if not cache.has("dogs"):
        r = requests.get(available_dogs_url)
        dogs = r.json()
        cache.set("dogs", dogs, timeout=3600)
    else:
        dogs = cache.get("dogs")

    return render_template("index.html", title="Home", dogs=dogs.get("collection"))


@main_blueprint.route("/dog/<string:dog_name>")
def dog(dog_name: str):
    PETSTABLISHED_BASE_URL = current_app.config['PETSTABLISHED_BASE_URL']
    PETSTABLISHED_PUBLIC_KEY = current_app.config['PETSTABLISHED_PUBLIC_KEY']

    dog_url = f"{PETSTABLISHED_BASE_URL}?public_key={PETSTABLISHED_PUBLIC_KEY}&search[name]={dog_name}"

    r = requests.get(dog_url)
    dog = r.json()
    # TODO: handle no dog returned
    return render_template("detail.html", dog=dog.get("collection")[0])
