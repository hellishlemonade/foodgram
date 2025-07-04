import csv

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from backend import settings
from recipes.models import Ingredient


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Path to file')

    def handle(self, *args, **options):
        success_count = 0
        with open(
                f'{settings.BASE_DIR}/data/ingredients.csv',
                'r',
                encoding='utf-8',
        ) as csv_file:
            reader = csv.reader(csv_file)

            for row in reader:
                name_csv = 0
                unit_csv = 1
                try:
                    obj, created = Ingredient.objects.get_or_create(
                        name=row[name_csv],
                        measurement_unit=row[unit_csv],
                    )
                    if created:
                        success_count += 1
                    if not created:
                        print(f'Ингредиенты {obj} уже есть в базе данных')
                except IntegrityError as err:
                    print(f'Ошибка {row}: {err}')
        print(f'{success_count} ингредиентов было импортировано')
