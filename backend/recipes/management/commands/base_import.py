import json

from django.conf import settings
from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    filename = None
    model = None

    def handle(self, *args, **options):
        data_path = settings.BASE_DIR / 'data' / self.filename
        try:
            with open(data_path, encoding='utf-8') as file:
                created = self.model.objects.bulk_create(
                    [self.model(**item) for item in json.load(file)],
                    ignore_conflicts=True
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'{data_path.name}: '
                    f'{len(created)} новых записей успешно загружено'
                )
            )
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Файл не найден: {data_path}'))
        except (json.JSONDecodeError, KeyError) as e:
            self.stderr.write(self.style.ERROR(f'Ошибка в файле: {e}'))
