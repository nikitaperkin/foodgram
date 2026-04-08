from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from django.urls import reverse
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Subscription, Tag, User)

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, UserRecipesSerializer,
                          TagSerializer)
from .services import build_shopping_cart


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


class UserViewSet(DjoserUserViewSet):

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user

        if request.method == 'DELETE':
            get_object_or_404(
                Subscription, user=user, following_id=id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = get_object_or_404(User, pk=id)
        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        _, created = Subscription.objects.get_or_create(user=user,
                                                        following=author)
        if not created:
            raise serializers.ValidationError(
                f'Уже подписан на {author.username}'
            )
        return Response(
            UserRecipesSerializer(author, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        authors = User.objects.filter(author_subscriptions__user=request.user)
        page = self.paginate_queryset(authors)
        return self.get_paginated_response(
            UserRecipesSerializer(
                page, many=True, context={'request': request}
            ).data
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'DELETE':
            if not user.avatar:
                raise serializers.ValidationError('Аватар отсутствует')
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        if 'avatar' not in request.data:
            raise serializers.ValidationError('Обязательное поле')
        serializer = AvatarSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_queryset(self):
        return (
            Recipe.objects.select_related('author')
            .prefetch_related('tags', 'recipe_ingredients__ingredient')
        )

    def _add_or_remove_recipe(self, request, model, pk=None):
        user = request.user
        if request.method == 'DELETE':
            get_object_or_404(model, user=user, recipe_id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное'
            )
        return Response(
            RecipeShortSerializer(
                recipe, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._add_or_remove_recipe(
            request=request,
            model=Favorite,
            pk=pk
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._add_or_remove_recipe(
            request=request,
            model=ShoppingCart,
            pk=pk
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise Http404
        return Response(
            {'short-link': request.build_absolute_uri(
                reverse('recipe-short-link', kwargs={'pk': pk})
            )}
        )

    @staticmethod
    def redirect_to_recipe(request, pk):
        return redirect(f'/recipes/{pk}/')

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        return FileResponse(
            build_shopping_cart(request.user),
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain',
        )
