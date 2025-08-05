from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField

# Form choices
AGE_CHOICES = [
    ("", "Any"),
    ("Puppy", "Puppy"),
    ("Young", "Young"),
    ("Adult", "Adult"),
    ("Senior", "Senior"),
]

SIZE_CHOICES = [
    ("", "Any"),
    ("Small", "Small"),
    ("Medium", "Medium"),
    ("Large", "Large"),
    ("X-Large", "X-Large"),
]

SHEDDING_CHOICES = [
    ("", "Any"),
    ("No shedding", "No Shedding"),
    ("Sheds a little", "Sheds a Little"),
    ("Sheds a lot", "Sheds a Lot"),
]


class SearchForm(FlaskForm):
    sex = SelectField(
        "Gender", choices=[("", "Any"), ("Male", "Male"), ("Female", "Female")]
    )
    age = SelectField("Age", choices=AGE_CHOICES)
    breed = SelectField("Breed", choices=[("", "Any")])
    size = SelectField("Size", choices=SIZE_CHOICES)
    shedding = SelectField("Shedding", choices=SHEDDING_CHOICES)
    is_ok_with_other_dogs = BooleanField("Good with Dogs")
    is_ok_with_other_cats = BooleanField("Good with Cats")
    is_ok_with_other_kids = BooleanField("Good with Kids")


class PaginationForm(FlaskForm):
    per_page = SelectField(
        "Results per Page:", choices=[(24, 24), (48, 48), (96, 96), (999, "All")]
    )
