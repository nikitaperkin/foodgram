from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, User, Tag)


class HasRelatedFilter(admin.SimpleListFilter):
    related_name = None

    def lookups(self, request, model_admin):
        return [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                **{f'{self.related_name}__isnull': False}
            ).distinct()
        if self.value() == 'no':
            return queryset.filter(
                **{f'{self.related_name}__isnull': True}
            )


class HasRecipesFilter(HasRelatedFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class HasSubscriptionsFilter(HasRelatedFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'subscriptions'


class HasFollowersFilter(HasRelatedFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_followers'
    related_name = 'author_subscriptions'


class RecipesCountMixin:
    @admin.display(description='Рецептов')
    def recipes_count(self, item):
        return item.recipes.count()


class UserRecipeMixin:
    list_display = ('id', 'user', 'recipe')


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'get_full_name', 'email',
        'get_avatar', 'recipes_count', 'subscriptions_count', 'followers_count'
    )
    list_filter = (
        'is_staff', HasRecipesFilter,
        HasSubscriptionsFilter, HasFollowersFilter
    )
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar',)}),
    )
    ordering = ('username',)

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, user):
        if not user.avatar:
            return '—'
        return (f'<img src="{user.avatar.url}" width="50" '
                f'height="50" style="border-radius: 50%">')

    @admin.display(description='Рецептов')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def followers_count(self, user):
        return user.author_subscriptions.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'following')
    ordering = ('user',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author',
        'favorites_count', 'get_ingredients', 'get_tags', 'get_image'
    )
    search_fields = (
        'name', 'author__username',
        'tags__name', 'ingredients__name'
    )
    list_filter = ('tags', )
    list_select_related = ('author',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'tags', 'recipe_ingredients__ingredient'
        )

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Продукты')
    @mark_safe
    def get_ingredients(self, recipe):
        return '<br>'.join(
            f'{ri.ingredient.name} — {ri.amount} '
            f'{ri.ingredient.measurement_unit}'
            for ri in recipe.recipe_ingredients.select_related('ingredient')
        )

    @admin.display(description='Теги')
    @mark_safe
    def get_tags(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Картинка')
    @mark_safe
    def get_image(self, recipe):
        if not recipe.image:
            return '—'
        return (f'<img src="{recipe.image.url}" width="60" '
                f'height="60" style="object-fit: cover">')


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', HasRecipesFilter)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(UserRecipeMixin, admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeMixin, admin.ModelAdmin):
    pass
