from recipes.models import Tag
from .base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Загрузка тегов из файла tags.json'
    filename = 'tags.json'
    model = Tag
