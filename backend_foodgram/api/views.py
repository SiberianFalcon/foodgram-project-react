from django.db.models import Sum
from django.db.models.expressions import Exists, OuterRef
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    SAFE_METHODS, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from .serializers import (
    FollowSerializer, IngredientSerializer, RecipeCreateSerializer,
    RecipeInfoSerializer, RecipeSerializer, TagSerializer,
    UserCreateSerializer, UserSerializer,
)
from .models import (
    FavoriteRecipe, Ingredient, IngredientsRecipe, Recipe, ShoppingList, Tag,
)
from .models import Follow, User


class UserViewSet(DjoserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(('GET',), detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == 'GET':
            return self.retrieve(request, *args, **kwargs)

    @action(('POST',), detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(('GET',), detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = request.user.follower.all()
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        ('POST', 'DELETE'), detail=True, permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user
        if request.method == 'POST':
            serializer = FollowSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(Follow, user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsOwnerOrReadOnly,)
    filterset_class = RecipeFilter

    def destroy(self, request, pk=None):
        instance = get_object_or_404(Recipe, id=pk)
        if not instance.author == request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe', 'in_shopping_list',
            'favorite_recipe',
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    self.request.user.favorited.filter(recipe=OuterRef('id'))
                ),
                is_in_shopping_cart=Exists(
                    self.request.user.user_shopping_list.filter(
                        recipe=OuterRef('id')
                    )
                ),
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        ('POST', 'DELETE'), detail=True, permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            FavoriteRecipe.objects.create(
                user=request.user, recipe=recipe
            )
            serializer = RecipeInfoSerializer(recipe)
            return Response(
                serializer.data,
                status.HTTP_201_CREATED,
            )
        if request.method == 'DELETE':
            get_object_or_404(
                FavoriteRecipe, user=request.user, recipe=recipe
            ).delete()
            return Response(
                {'errors': 'Recipe has been removed from your favorites'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        ('POST', 'DELETE'), detail=True, permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            ShoppingList.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeInfoSerializer(recipe)
            return Response(
                serializer.data,
                status.HTTP_201_CREATED,
            )
        if request.method == 'DELETE':
            get_object_or_404(
                ShoppingList, user=request.user, recipe=recipe
            ).delete()
            return Response(
                {'errors': ('Recipe has been removed '
                            'from your shopping list')},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(('GET',), detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = IngredientsRecipe.objects.all()
        ingredients = ingredients.values(
            'ingredient__name',
            'ingredient__measurement_unit'
        )
        shopping_list = ingredients.filter(
            recipe__in_shopping_list__user=request.user
        ).annotate(ingredient_total=Sum('amount'))
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        response.write(f"{request.user.username}'s shopping list\n\n")
        for ingredient in shopping_list:
            ingredients = ''.join(
                f'{ingredient.get("ingredient__name")} - '
                f'{ingredient.get("ingredient_total")}'
                f'{ingredient.get("ingredient__measurement_unit")}\n'
            )
            response.write(f'{ingredients}')

        return response