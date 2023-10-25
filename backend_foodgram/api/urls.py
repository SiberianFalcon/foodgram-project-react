from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework import routers

from .views import (
    CustomUserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet)

app_name = 'api'

router = routers.DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('token/login/', TokenCreateView.as_view(), name='login'),
    path('token/logout/', TokenDestroyView.as_view(), name='logout'),
]
