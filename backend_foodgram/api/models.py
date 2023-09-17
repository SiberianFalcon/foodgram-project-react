from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField(_("first name"), max_length=150, blank=False, null=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False, null=False)
    email = models.EmailField(_("email address"), max_length=150, blank=False, null=False, unique=False)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        abstract = True

    

class Tag(models.Model):
    color = models.CharField(max_length=16)
    name = models.CharField(max_length=64, null=False)
    slug = models.SlugField(null=False)



class Ingridients(models.Model):
    amount = models.PositiveSmallIntegerField()
    name = models.CharField()
    measurement_unit = models.CharField(max_length=10)


class Recipe(models.Model):
    author = models.ForeignKey(User, related_name="author", on_delete=models.CASCADE)
    tag = models.ManyToManyField(Tag, related_name='tag')
    text = models.TextField()
    name = models.CharField(max_length=128, null=False)
    ingridients = models.ManyToManyField(Ingridients)
    image = models.ImageField()
    cooking_time = models.CharField()


class Subscription(models.Model):
    name = models.ManyToManyField(User)
    is_subscribed = models.BooleanField(default=False)
