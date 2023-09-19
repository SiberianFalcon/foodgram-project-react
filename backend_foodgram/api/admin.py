from django.contrib import admin


from api.models import User, Tag, Ingredient, Recipe, IngredientsRecipe, Follow


admin.site.register(User)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(IngredientsRecipe)
admin.site.register(Follow)