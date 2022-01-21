import csv
from django.core.management import BaseCommand
from zone.models import Tag

class Command(BaseCommand):
    help = 'import a csv of the generated site tag information'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path')
    
    def handle(self, *args, **options):
        with open(options['csv_file_path']) as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if row[1]:
                        tag, created_t = Tag.objects.update_or_create(
                            slug = row[0],
                            defaults = {'description': row[1]}
                        )
                    else:
                        tag, created_t = Tag.objects.update_or_create(
                            slug = row[0],
                            defaults = {'description': row[0]}
                        )

