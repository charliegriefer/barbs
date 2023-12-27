from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField
from wtforms.validators import DataRequired


age_choices = [("", "Any"), ("Puppy", "Puppy"), ("Young", "Young"), ("Adult", "Adult"), ("Senior", "Senior")]
size_choices = [("", "Any"), ("Small", "Small"), ("Medium", "Medium"), ("Large", "Large"), ("X-Large", "X-Large")]
shed_choices = [("", "Any"),
                ("No shedding", "No Shedding"), ("Sheds a little", "Sheds a Little"), ("Sheds a lot", "Sheds a Lot")]

class SearchForm(FlaskForm):
    sex = SelectField("Gender", choices=[("", "Any"), ("Male", "Male"), ("Female", "Female")])
    age = SelectField("Age", choices = age_choices)
    breed = SelectField("Breed", choices=[("", "Any")])
    size = SelectField("Size", choices=size_choices)
    shedding = SelectField("Shedding", choices=shed_choices)
    is_ok_with_other_dogs = BooleanField("Good with Dogs")
    is_ok_with_other_cats = BooleanField("Good with Cats")
    is_ok_with_other_kids = BooleanField("Good with Kids")

class PaginationForm(FlaskForm):
    per_page = SelectField("Results per Page:", choices=[25, 50, 100, "All"])
