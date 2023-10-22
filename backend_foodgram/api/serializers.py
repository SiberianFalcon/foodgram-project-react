from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
# 
from django.shortcuts import get_object_or_404
from django.db.models import F
from rest_framework.fields import SerializerMethodField
# 
from recipe.models import (
    Favorite, Ingredient, Recipe,
    RecipeIngredient, Subscription, Tag)

MIN_VALUE = 1
MAX_VALUE = 32000

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'password', 'username',
                  'first_name', 'last_name')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context['request']
        user = request.user
        if not user.is_authenticated:
            return False
        return user.subscriptions.filter(following=obj).exists()


class SubscriptionSerializer(CustomUserSerializer):
    email = serializers.EmailField()
    username = serializers.StringRelatedField()
    first_name = serializers.StringRelatedField()
    last_name = serializers.StringRelatedField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipe', 'recipes_count')

    def get_recipes(self, obj):
        recipes = obj.recipe.all()
        serializer = RecipeInFavoriteSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        recipes = obj.recipe.all()
        return recipes.count()


class ShortSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('follower', 'following')

    def validate(self, data):
        follower = data.get('follower')
        following = data.get('following')
        if follower.subscriptions.filter(following=following).exists():
            raise ValidationError('Подписка уже существует')
        if follower == following:
            raise ValidationError(
                'Вы не можете подписаться на самого себя')
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(instance.following, context={
            'request': self.context.get('request')}).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


# class IngredientInRecipeSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(source='ingredient.id')
#     name = serializers.ReadOnlyField(source='ingredient.name')
#     measurement_unit = serializers.ReadOnlyField(
#         source='ingredient.measurement_unit')
#     amount = serializers.IntegerField(
#         min_value=MIN_VALUE, max_value=MAX_VALUE)

#     class Meta:
#         model = RecipeIngredient
#         fields = ('id', 'name', 'measurement_unit', 'amount')

class IngredientForRecipeSerializer(serializers.ModelSerializer):
    """Связывающий сериализатор для создания ингридиентов в рецепте."""

    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода рецептов и их параметров c 3 методами:
    1) get_ingredients - для вывода описания продукта поля ingredients.
    2) get_is_in_shopping_cart - для определении рецепта в покупках,
    если пользователь добавил рецепт в список покупок - True, если нет - False.
    3) get_is_favorited - для определении рецепта в избранном,
    если пользователь добавил рецепт в избранное - True, если нет - False.
    """

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    is_favorited = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values().annotate(
            amount=F('ingredient_recipe__amount')
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.recipes_in_shopping_cart.filter(recipe=obj).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.favorited.filter(recipe=obj).exists()
        return False


class CreateRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создание или обновление рецепта с 2 методами:
    1) create - Для создания рецепта.
    2) update - Для обновления рецепта
    """

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = IngredientForRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time',
        )

    def validate(self, data):
        if 'ingredients' not in data:
            raise ValidationError({'ingredients': 'Обязательное поле!'})
        elif 'tags' not in data:
            raise ValidationError({'tags': 'Обязательное поле!'})
        elif 'cooking_time' not in data:
            raise ValidationError({'cooking_time': 'Обязательное поле!'})
        return data

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Нужно выбрать Тег!')
        tags_list = []
        for tag in value:
            if tag in tags_list:
                raise ValidationError('Тег уже добавлен!')
            tags_list.append(tag)
        return value

    def validate_ingredients(self, ingredients):
        ingredient_id = Ingredient.objects.values_list('id', flat=True)
        for ing in ingredients:
            if ing['id'] not in ingredient_id:
                raise ValidationError(
                    'Такого ингредиента не существует!'
                )
        if not ingredients:
            raise ValidationError(
                'Нужно добавить ингредиенты!'
            )
        ingredients_list = []
        for product in ingredients:
            ingredient = get_object_or_404(Ingredient, id=product['id'])
            if ingredient in ingredients_list:
                raise ValidationError(
                    'Этот ингредиент добавлен!'
                )
            elif 'amount' not in product:
                raise ValidationError({
                    'amount': 'обязательное поле!'
                })
            ingredients_list.append(ingredient)
        return ingredients

    def validate_image(self, image):
        if not image:
            raise ValidationError({'image': 'Обязательное поле!'})
        return image

    def validate_cooking_time(self, cooking_time):
        if not cooking_time:
            raise ValidationError(
                'Нужно написать время приготовления!'
            )
        return cooking_time

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            **validated_data,
            author=self.context.get('request').user,
        )
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredients_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
                recipe=recipe)
        return recipe

    def update(self, recipe, validated_data):
        recipe.tags.clear()
        recipe.ingredients.clear()
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredients_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
                recipe=recipe
            )
        return super().update(recipe, validated_data)



# class RecipeSerializer(serializers.ModelSerializer):
#     tags = serializers.SerializerMethodField()
#     author = serializers.SerializerMethodField()
#     image = Base64ImageField()
#     ingredients = IngredientInRecipeSerializer(many=True)
#     is_favorited = serializers.SerializerMethodField()
#     is_in_shopping_cart = serializers.SerializerMethodField()
#     cooking_time = serializers.IntegerField(min_value=MIN_VALUE,
#                                             max_value=MAX_VALUE)

#     class Meta:
#         model = Recipe
#         fields = ('id', 'tags', 'author', 'ingredients',
#                   'is_favorited', 'is_in_shopping_cart',
#                   'name', 'image', 'text', 'cooking_time')

#     def get_user(self):
#         request = self.context.get('request')
#         return request.user

#     def get_tags(self, recipe):
#         if self.context['request'].method in ['POST', 'PATCH']:
#             return recipe.tags.values_list('id', flat=True)
#         tags = TagSerializer(recipe.tags.all(), many=True)
#         return tags.data

#     def get_author(self, obj):
#         author = obj.author
#         author_serializer = CustomUserSerializer(
#             author,
#             context=self.context
#         )
#         return author_serializer.data

#     def get_is_favorited(self, obj):
#         user = self.context.get('request').user
#         if user.is_authenticated:
#             return user.favorited.filter(recipe=obj).exists()
#         return False

#     def get_is_in_shopping_cart(self, obj):
#         user = self.get_user()
#         if user.is_authenticated:
#             return user.recipes_in_shopping_cart.filter(
#                 recipe=obj).exists()
#         return False

#     def validate(self, data):
#         tags_ids = self.initial_data.get("tags")
#         ingredients = self.initial_data.get("ingredients")
#         if not tags_ids or not ingredients:
#             raise ValidationError("Недостаточно данных.")
#         if data['ingredients'] is None:
#             raise ValidationError('Ингредиенты - Обязательное поле!')
#         elif data['cooking_time'] is None:
#             raise ValidationError('Время готовки - Обязательное поле!')
#         elif data['image'] is None:
#             raise ValidationError('Картинка - Обязательное поле!')
#         elif data['name'] is None:
#             raise ValidationError('Название - Обязательное поле!')
#         elif data['text'] is None:
#             raise ValidationError('Описание - Обязательное поле!')
#         return data

#     def update_or_create_ingredient_amount(self, validated_data, recipe):
#         if not validated_data:
#             raise serializers.ValidationError(
#                 'Такого ингредиента не существует')

#         goods = []
#         for i in validated_data:
#             goods.append(i.get('id'))
#         if len(goods) != len(set(goods)):
#             raise serializers.ValidationError(
#                 'Ингредиенты не могут повторяться')

#         recipe_ingredients = [
#             RecipeIngredient(
#                 ingredient_id=ingredient['id'], amount=ingredient['amount'],
#                 recipe=recipe) for ingredient in validated_data]
#         RecipeIngredient.objects.bulk_create(recipe_ingredients)

#     def create(self, validated_data):
#         ingredients_data = self.initial_data.pop('ingredients', '')
#         validated_data.pop('ingredients', '')
#         recipe = Recipe.objects.create(
#             image=validated_data.pop('image'), **validated_data)
#         tags_data = self.initial_data.get('tags')
#         recipe.tags.set(tags_data)
#         self.update_or_create_ingredient_amount(ingredients_data, recipe)
#         return recipe

#     def update(self, recipe, validated_data):
#         recipe.image = validated_data.get('image', recipe.image)
#         recipe.name = validated_data.get('name', recipe.name)
#         recipe.text = validated_data.get('text', recipe.text)
#         recipe.cooking_time = validated_data.get(
#             'cooking_time', recipe.cooking_time)
#         recipe.tags.clear()
#         tags_data = self.initial_data.get('tags')
#         recipe.tags.set(tags_data)
#         recipe.ingredients.all().delete()
#         self.update_or_create_ingredient_amount(
#             self.initial_data.get('ingredients'), recipe)
#         recipe.save()
#         return recipe


class RecipeInFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only = ('id', 'name', 'image', 'cooking_time')


class ShortRecipeInFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if user.favorite_recipes.filter(recipe=recipe).exists():
            raise ValidationError(
                {'error': 'This recipe is already in favorites.'})
        return data

    def to_representation(self, instance):
        return RecipeInFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')}).data
