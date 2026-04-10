from datetime import date

from django.db.models import Sum
from django.template.loader import render_to_string

from recipes.models import Recipe, RecipeIngredient


def build_shopping_cart(user):
    return render_to_string('shopping_cart.txt', {
        'date': date.today(),
        'ingredients': RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')),
        'recipes': (
            Recipe.objects
            .filter(shoppingcarts__user=user)
            .select_related('author')
            .prefetch_related('tags')
        )
    })
