from django.shortcuts import render
from rest_framework import filters, viewsets
from rest_framework.decorators import action


from .models import Recipe, Ingridient

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()


class IngridientViewSet(viewsets.ModelViewSet):
    queryset = Ingridient.objects.all()


