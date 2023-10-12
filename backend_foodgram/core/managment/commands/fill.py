import csv

from django.core.management.base import BaseCommand

from api.models import Ingredient
from . import ingredients


class Command(BaseCommand):

    def handle(self, *args, **options):
        with open(ingredients, 'r', encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            ingredient_list = [Ingredient(
                name=name, measurement_unit=measurement_unit)
                for name, measurement_unit in csv_reader]

            Ingredient.objects.bulk_create(ingredient_list)