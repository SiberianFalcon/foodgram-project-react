from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


from .constants import MAX_LENGHT_FOR_EMAIL, MAX_LENGHT


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, first_name,
                    last_name, password=None):
        if not email:
            raise ValueError('Email обязателен')

        user = self.model(
            email=self.normalize_email(email), username=username,
            first_name=first_name, last_name=last_name,)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name,
                         last_name, password=None):
        user = self.create_user(
            email, password=password, username=username,
            first_name=first_name, last_name=last_name,)
        user.is_admin = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    email = models.EmailField(
        'email address', max_length=MAX_LENGHT_FOR_EMAIL, unique=True)
    username = models.CharField(
        max_length=MAX_LENGHT, unique=True, help_text=(
            'Обязательно. Не более MAX_LENGHT знаков.'
            'Применимы только латинские буквы, цифры и символы @/./+/-/_'),
        validators=[UnicodeUsernameValidator],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует', })
    first_name = models.CharField('first name', max_length=MAX_LENGHT)
    last_name = models.CharField('last name', max_length=MAX_LENGHT)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
