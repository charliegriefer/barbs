from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import DataRequired


age_choices = [("", "Any"), ("Puppy", "Puppy"), ("Young", "Young"), ("Adult", "Adult"), ("Senior", "Senior")]

class SearchForm(FlaskForm):
    gender = SelectField("Gender", choices=[("", "Any"), ("Male", "Male"), ("Female", "Female")])
    age = SelectField("Age", choices = age_choices)
