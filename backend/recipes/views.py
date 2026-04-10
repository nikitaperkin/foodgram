from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def redirect_to_recipe(request, pk):
    get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{pk}/')
