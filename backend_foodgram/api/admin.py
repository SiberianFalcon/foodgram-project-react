from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin


from .models import (
    Favorite, Ingredient, Recipe, 
    RecipeIngredient, ShoppingCart, Subscription, Tag)

admin.site.register(Tag)
admin.site.register(Subscription)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = ['id', 'name']


# class IngredientAdmin(admin.ModelAdmin):
#     inlines = (RecipeIngredientInline, )

class IngredientResource(resources.ModelResource):
    """Управление Ингридиентами через админку."""

    class Meta:
        model = Ingredient


class IngredientAdmin(ImportExportModelAdmin):
    """Загрузка Ингридиентов из файла через админку."""

    resource_class = IngredientResource
    list_display = (
        "name",
        "measurement_unit",
    )
    search_fields = ("name",)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)
admin.site.register(IngredientAdmin)