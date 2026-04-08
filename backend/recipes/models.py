from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

MIN_COOKING_TIME = 1
MIN_AMOUNT = 1


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Ник',
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Допустимы только буквы, цифры и символы @.+-_'
            )
        ],
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=254,
        unique=True,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/images/',
        null=True,
        default=None
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=150
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='author_subscriptions')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follower'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на: {self.following}'


class UserRecipeBase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Название', max_length=128)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_measurement_unit'
            )
        ]


class Tag(models.Model):
    name = models.CharField(
        max_length=32, unique=True, verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=32, unique=True, verbose_name='Slug (идентификатор)'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название', max_length=256)
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/',
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(
            MIN_AMOUNT,
            message=f'Минимальное время приготовления: {MIN_COOKING_TIME} мин.'
        )]
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тег')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиенты')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f'Количество не может быть меньше {MIN_AMOUNT}.'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        default_related_name = 'recipe_ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class Favorite(UserRecipeBase):
    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(UserRecipeBase):
    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине покупок'
