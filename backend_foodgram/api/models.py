from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, EmailValidator


class User(AbstractUser):
    """Самодельная модель пользователя."""

    first_name = models.CharField(
        ("first name"), max_length=150, blank=False, null=False
    )
    last_name = models.CharField(
        ("last name"), max_length=150, blank=False, null=False
    )
    email = models.EmailField(
        ("email address"), max_length=254, blank=False, null=False,
        unique=True, validators=[EmailValidator]
    )
    is_staff = models.BooleanField(
        ("staff status"), default=False,
        help_text=(
            "Designates whether the user can log into this admin site.")
    )
    is_active = models.BooleanField(
        ("active"), default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts.")
    )

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "username"]


class Tag(models.Model):
    """Модель тегов для рецептов."""

    color = models.CharField(
        max_length=7, blank=False, null=False, unique=True,
        validators=[RegexValidator]
    )
    name = models.CharField(
        max_length=200, blank=False, null=False, unique=True
    )
    slug = models.SlugField(
        max_length=200, blank=False, null=False, unique=True
    )


class Ingredient(models.Model):
    """Модель ингридиентов для рецептов."""

    measurement_unit = models.CharField(max_length=10, blank=False)
    name = models.CharField(max_length=128, blank=False)


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User, related_name="author", on_delete=models.CASCADE,
        blank=False, null=False
    )
    name = models.CharField(max_length=128, blank=False, null=False)
    image = models.ImageField(blank=False, null=False)
    text = models.TextField(blank=False, null=False)
    ingredient = models.ManyToManyField(
        Ingredient, blank=False, through='IngredientsRecipe'
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.RESTRICT, blank=False,
        null=False, related_name='recipes'
    )
    cooking_time = models.TimeField(blank=False, null=False)


class IngredientsRecipe(models.Model):
    """
    Модель связующая рецепты и ингридиенты, благодаря которой
    считается количество необходимых продуктов для нужного рецепта."""

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.RESTRICT, related_name='recipes'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.RESTRICT, related_name='ingredients'
    )
    amount = models.PositiveSmallIntegerField()


class Follow(models.Model):
    """Модель подписчиков."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )
