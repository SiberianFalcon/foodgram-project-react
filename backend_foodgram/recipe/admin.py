from django.contrib import admin
from import_export import resources
from django.core.exceptions import ValidationError
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
    list_display = ('id', 'name')


class BookResource(resources.ModelResource):

    class Meta:
        model = Ingredient


class IngredientExport(ImportExportModelAdmin):
    resource_classes = [BookResource]


class TagValidator(admin.ModelAdmin):

    class Meta:
        model = Tag

    def tag_validator(self):
        if Tag.objects.exclude(id=self.id).filter(color=self.color).exists():
            raise ValidationError('Данный цвет уже существует')


admin.site.register(Favorite)
admin.site.register(Subscription)
admin.site.register(ShoppingCart)
admin.site.register(Tag, TagValidator)
admin.site.register(RecipeIngredient)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientExport)
