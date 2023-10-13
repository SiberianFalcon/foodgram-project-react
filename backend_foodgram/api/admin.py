from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    Favorite, Ingredient, Recipe,
    RecipeIngredient, ShoppingCart, Subscription, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = ['id', 'name']


class BookResource(resources.ModelResource):

    class Meta:
        model = Ingredient


class IngredientExport(ImportExportModelAdmin):
    resource_classes = [BookResource]


admin.site.register(Tag)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Subscription)
admin.site.register(RecipeIngredient)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientExport)
