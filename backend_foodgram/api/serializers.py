import base64

from django.core.files.base import ContentFile
from django.db.transaction import atomic
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from .models import Ingredient, IngredientsRecipe, Recipe, Tag
from .models import Follow, User


MIN_VALUE = 1
MAX_VALUE = 32_000


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'password', 'first_name', 'last_name'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError('Invalid username')
        return value


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.following.filter(user=request.user).exists()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')


class FollowRepresentationSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.follower.exists()

    def get_recipes(self, obj):
        queryset = obj.recipe.all()
        serializer = RecipeInfoSerializer(queryset, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipe.count()


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def to_representation(self, instance):
        request = self.context.get('request')
        return FollowRepresentationSerializer(
            instance.author, context={'request': request}
        ).data

    def create(self, validated_data):
        user = self.context['request'].user
        author = validated_data['author']

        if user.follower.filter(author=author).exists():
            raise ValidationError(
                'Already subscribed',
                code=status.HTTP_400_BAD_REQUEST
            )

        if user == author:
            raise ValidationError(
                'Unable to subscribe to yourself',
                code=status.HTTP_400_BAD_REQUEST
            )

        follow = Follow.objects.create(user=user, author=author)
        return follow


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = (
            UniqueTogetherValidator(
                queryset=IngredientsRecipe.objects.all(),
                fields=('recipe', 'ingredient',)
            ),
        )


class AddIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_VALUE, max_value=MAX_VALUE
    )

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'amount')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE, max_value=MAX_VALUE
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'image', 'tags', 'author', 'ingredients', 'name', 'text',
            'cooking_time'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        unique_ingredients = set()
        for ingredient in ingredients:
            current_ingredient = ingredient['id']
            if current_ingredient in unique_ingredients:
                raise serializers.ValidationError(
                    'No duplicate ingredients'
                )
            unique_ingredients.add(current_ingredient)
        return data

    def add_ingredients(self, ingredients, recipe):
        ingredients_in_recipe = []
        for ingredient in ingredients:
            ingredients_in_recipe.append(
                IngredientsRecipe(
                    recipe=recipe,
                    ingredient=ingredient.get('id'),
                    amount=ingredient.get('amount'),
                )
            )
        IngredientsRecipe.objects.bulk_create(ingredients_in_recipe)

    @atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return recipe

    @atomic
    def update(self, obj, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            obj.ingredients.clear()
            self.add_ingredients(ingredients, obj)

        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            obj.tags.set(tags)

        return super().update(obj, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance, context=self.context)
        return serializer.data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = IngredientInRecipeSerializer(
        many=True, required=True, source='recipe'
    )
    image = serializers.SerializerMethodField('get_image_url', read_only=True,)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )


class RecipeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')