from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import AuthenticationFailed
from django import forms
from recipe.models import Recipe, Tag

User = get_user_model()


class TagsField(forms.MultipleChoiceField):
    def validate(self, value):
        pass


class TagsFilter(filters.MultipleChoiceFilter):
    field_class = TagsField


class RecipeFilter(FilterSet):
    tags = TagsFilter(method='get_tags')
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart', method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_tags(self, queryset, name, value):
        queryset = queryset.filter(tags__slug__in=value).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_anonymous:
            raise AuthenticationFailed(detail='Нужно авторизоваться!')
        if value:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_anonymous:
            raise AuthenticationFailed(detail='Нужно авторизоваться!')
        if value:
            return queryset.filter(shopping_by__user=self.request.user)
        return queryset


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'
