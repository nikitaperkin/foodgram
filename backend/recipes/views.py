from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def redirect_to_recipe(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'Рецепт id={pk} не найден')
    return redirect(f'/recipes/{pk}/')
