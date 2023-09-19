from django.shortcuts import render
from rest_framework import filters, viewsets
from rest_framework.decorators import action


from .models import Recipe, Ingredient
from .serializers import IngredientSerializer

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


