from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
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
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.subscriptions.filter(following=obj).exists()
        return False


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        count_limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if count_limit:
            recipes = recipes[:int(count_limit)]
        serializer = RecipeInFavoriteSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        recipes = obj.recipes.all()
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


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        min_value=MIN_VALUE, max_value=MAX_VALUE)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientInRecipeSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(min_value=MIN_VALUE,
                                            max_value=MAX_VALUE)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

        read_only_fields = (
            "is_favorite",
            "is_shopping_cart",
        )

    def get_user(self):
        request = self.context.get('request')
        return request.user

    def get_tags(self, recipe):
        if self.context['request'].method in ['POST', 'PATCH']:
            return recipe.tags.values_list('id', flat=True)
        tags = TagSerializer(recipe.tags.all(), many=True)
        return tags.data

    def get_author(self, obj):
        author = obj.author
        author_serializer = CustomUserSerializer(
            author,
            context=self.context
        )
        return author_serializer.data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated:
            return user.favorite_recipes.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.get_user()
        if user.is_authenticated:
            return user.recipes_in_shopping_cart.filter(
                recipe=obj).exists()
        return False

    def validate(self, data):
        tags_id = self.initial_data.get('tags')
        ingredients = self.initial_data.get("ingredients")
        ingredients_id = Ingredient.objects.values_list('id', flat=True)

        for i in ingredients:
            if i.get('id') not in ingredients_id:
                raise ValidationError('Такого ингредиента не существует!')

        if data['ingredients'] is None:
            raise ValidationError('Ингредиенты - Обязательное поле!')
        elif data['cooking_time'] is None:
            raise ValidationError('Время готовки - Обязательное поле!')
        elif data['image'] is None:
            raise ValidationError('Картинка - Обязательное поле!')
        elif data['name'] is None:
            raise ValidationError('Название - Обязательное поле!')
        elif data['text'] is None:
            raise ValidationError('Описание - Обязательное поле!')
        elif not tags_id or not ingredients:
            raise ValidationError('Нет такого тега или ингредиента')
        return data

    def update_or_create_ingredient_amount(self, validated_data, recipe):
        if not validated_data:
            raise serializers.ValidationError(
                'Необходим ингредиент')

        goods = []
        for i in validated_data:
            goods.append(i.get('id'))
        if len(goods) != len(set(goods)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться')

        recipe_ingredients = [
            RecipeIngredient(
                ingredient_id=ingredient['id'], amount=ingredient['amount'],
                recipe=recipe) for ingredient in validated_data]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = self.initial_data.pop('ingredients', '')
        validated_data.pop('ingredients', '')
        recipe = Recipe.objects.create(
            image=validated_data.pop('image'), **validated_data)
        tags_data = self.initial_data.get('tags')
        recipe.tags.set(tags_data)
        self.update_or_create_ingredient_amount(ingredients_data, recipe)
        return recipe

    def update(self, recipe, validated_data):
        recipe.image = validated_data.get('image', recipe.image)
        recipe.name = validated_data.get('name', recipe.name)
        recipe.text = validated_data.get('text', recipe.text)
        recipe.cooking_time = validated_data.get(
            'cooking_time', recipe.cooking_time)
        recipe.tags.clear()
        tags_data = self.initial_data.get('tags')
        recipe.tags.set(tags_data)
        recipe.ingredients.all().delete()
        self.update_or_create_ingredient_amount(
            self.initial_data.get('ingredients'), recipe)
        recipe.save()
        return recipe


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
