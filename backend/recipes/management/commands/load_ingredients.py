import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из файла ingredients.json'

    def handle(self, *args, **options):
        data_path = os.path.join(
            settings.BASE_DIR.parent, 'data', 'ingredients.json'
        )

        if not os.path.exists(data_path):
            self.stderr.write(self.style.ERROR(f'Файл не найден: {data_path}'))
            return

        with open(data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            ingredients = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                for item in data
            ]
            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно загружено {len(ingredients)} ингредиентов!'
            )
        )
