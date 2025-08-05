import os

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

from forms import PaginationForm, SearchForm
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
    # Get dogs and initialize forms
    available_dogs = dog_service.get_available_dogs()
    search_form = SearchForm()
    pagination_form = PaginationForm()

    # Populate breed choices dynamically
    breeds = dog_service.get_dog_breeds(available_dogs)
    search_form.breed.choices = [("", "Any")] + [(breed, breed) for breed in breeds]

    # Handle pagination
    per_page = int(request.args.get("per_page", 24))
    if request.args.get("per_page") == "999":
        per_page = len(available_dogs)
        pagination_form.per_page.process_data(999)
    else:
        pagination_form.per_page.process_data(per_page)

    current_page = int(request.args.get("current_page", 1))

    # Apply filters
    filters = {
        key: value
        for key, value in request.args.items()
        if key in ["sex", "age", "size", "shedding", "breed"] and value
    }

    filtered_dogs = dog_service.filter_dogs(available_dogs, filters)
    total_dogs = len(filtered_dogs)

    # Apply pagination
    paginated_dogs, number_of_pages = dog_service.paginate_dogs(
        filtered_dogs, current_page, per_page
    )

    # Update form with current values
    for key, value in filters.items():
        if hasattr(search_form, key):
            getattr(search_form, key).process_data(value)

    # Build query string for pagination links
    query_string = build_query_string(request.args)

    return render_template(
        "index.html",
        title="Adopt | Puerto Peñasco | Barb's Dog Rescue",
        pagination_form=pagination_form,
        search_form=search_form,
        dogs=paginated_dogs,
        total_dogs=total_dogs,
        current_page=current_page,
        per_page=per_page,
        number_of_pages=number_of_pages,
        calculate_page_link=calculate_page_link,
        qs=query_string,
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


@app.route("/debug-static")
def debug_static():
    """Debug static file configuration"""
    return f"""
    <h3>Flask Static Debug Info:</h3>
    <p><strong>Static folder:</strong> {app.static_folder}</p>
    <p><strong>Static URL path:</strong> {app.static_url_path}</p>
    <p><strong>Root path:</strong> {app.root_path}</p>
    <p><strong>Instance path:</strong> {app.instance_path}</p>
    <br>
    <p><a href="/static/css/barbs.css">Test CSS link</a></p>
    """


if __name__ == "__main__":
    app.run(debug=True)
