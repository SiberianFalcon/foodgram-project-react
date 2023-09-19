from rest_framework import serializers
from rest_framework.relations import SlugRelatedField


from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    

    class Meta:
        fields = 'id', 'ingredient', 'measurement_unit'
        model = Ingredient