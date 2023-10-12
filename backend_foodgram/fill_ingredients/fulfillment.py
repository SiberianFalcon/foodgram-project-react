import csv
import os

from django.conf import settings

from . import ingredients
from api.models import Ingredient



def add_ingredient_objects_in_database(self, *args, **options):
    path = os.path.join(settings.BASE_DIR, 'fill_ingredients')
    with open(ingredients, 'r', encoding="utf-8") as file:
        csv_reader = csv.reader(file)
        ingredient_list = [
            Ingredient(name=name,
                       measurement_unit=measurement_unit)
            for name, measurement_unit in csv_reader
        ]
        Ingredient.objects.bulk_create(ingredient_list)