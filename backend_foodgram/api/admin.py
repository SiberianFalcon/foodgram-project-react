from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag)


from import_export.admin import ImportExportModelAdmin


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = ['id', 'name']


class IngredientAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline, )



class BookAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    ...

admin.site.register(Ingredient, BookAdmin)


admin.site.register(Tag)
admin.site.register(Subscription)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Recipe)

admin.site.register(RecipeIngredient, RecipeAdmin)