import os

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

# Forms are now created by the service layer
from services import DogService
from utils import build_query_string, calculate_page_link

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path, verbose=True)

# Create Flask app
app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["PETSTABLISHED_BASE_URL"] = "https://petstablished.com/api/v2/public/pets"
app.config["PETSTABLISHED_PUBLIC_KEY"] = os.environ["PETSTABLISHED_PUBLIC_KEY"]

# Initialize extensions
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})
csrf = CSRFProtect(app)

# Initialize services
dog_service = DogService(cache)


@app.before_request
def load_available_dogs():
    """Load dogs from API before each request"""
    dog_service.load_available_dogs()


@app.route("/")
def index():
    """Main search page with filtering and pagination"""
    # Get all search data from service
    search_data = dog_service.process_search_request(request.args)

    # Get pre-configured forms from service
    search_form, pagination_form = dog_service.prepare_forms(search_data)

    # Just render - zero business logic
    return render_template(
        "index.html",
        title="Adopt | Puerto Peñasco | Barb's Dog Rescue",
        search_form=search_form,
        pagination_form=pagination_form,
        dogs=search_data["dogs"],
        total_dogs=search_data["total_dogs"],
        current_page=search_data["current_page"],
        per_page=search_data["per_page"],
        number_of_pages=search_data["number_of_pages"],
        calculate_page_link=calculate_page_link,
        qs=build_query_string(request.args),
    )


@app.route("/detail/<int:dog_id>")
def dog_detail(dog_id: int):
    """Individual dog detail page"""
    dog = dog_service.get_dog_by_id(dog_id)

    if not dog:
        return render_template("404.html"), 404

    return render_template(
        "detail.html",
        title=f"Adopt | Puerto Peñasco | Barb's Dog Rescue | {dog.get('name')}",
        dog=dog,
    )


@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template("404.html"), 404


if __name__ == "__main__":
    # Only enable debug mode in development
    debug_mode = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(debug=debug_mode)
