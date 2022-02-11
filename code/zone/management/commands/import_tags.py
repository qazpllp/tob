import csv
from django.core.management import BaseCommand
from zone.models import Tag

class Command(BaseCommand):
    help = 'import a csv of the generated site tag information, and saves tags to model'

    def handle(self, *args, **options):
        with open('zone/static/zone/tags_mapping.txt') as f:
                reader = csv.reader(f)
                for row in reader:
                    tag, created_t = Tag.objects.update_or_create(
                        slug = row[0],
                        description = row[1],
                        # category = row[2]
                        defaults = {'category': row[2]}
                    )
