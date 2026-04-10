from recipes.models import Ingredient
from .base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Загрузка ингредиентов из файла ingredients.json'
    filename = 'ingredients.json'
    model = Ingredient
