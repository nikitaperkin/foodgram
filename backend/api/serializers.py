from collections import Counter

from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, MIN_AMOUNT, MIN_COOKING_TIME,
                            Recipe, RecipeIngredient, ShoppingCart,
                            Subscription, Tag, User)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            *DjoserUserSerializer.Meta.fields, 'is_subscribed', 'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Subscription.objects.filter(
                following=author, user=request.user
            ).exists()
        )


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, author):
        return RecipeShortSerializer(
            author.recipes.all()[
                :int(self.context.get('request').query_params.get(
                    'recipes_limit', 10**10
                ))
            ],
            many=True,
            context=self.context
        ).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar', )


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = fields

    def _user_has_recipe(self, recipe, model):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and model.objects.filter(
                recipe=recipe, user=request.user
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self._user_has_recipe(recipe=recipe, model=Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._user_has_recipe(recipe=recipe, model=ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_null=False,
        allow_empty=False
    )
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def _get_duplicates(self, items):
        return {item for item, count in Counter(items).items() if count > 1}

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент')
        ingredient_ids = [item['id'] for item in ingredients]
        duplicates = self._get_duplicates(ingredient_ids)
        if duplicates:
            raise serializers.ValidationError(
                f'Ингредиенты не должны повторяться: {duplicates}'
            )

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError('Нужен хотя бы один тег.')
        duplicates = self._get_duplicates(tags)
        if duplicates:
            raise serializers.ValidationError(
                f'Теги не должны повторяться: {duplicates}'
            )

        return data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Поле image обязательно.')
        return value

    def _save_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.recipe_ingredients.all().delete()
        self._save_ingredients(instance, validated_data.pop('ingredients'))
        instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context=self.context
        ).data
