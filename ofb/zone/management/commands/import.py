import csv
from turtle import title
from django.core.management import BaseCommand
from zone.models import Author, Story

class Command(BaseCommand):
    help = 'import a csv of the generated site data'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path')
    
    def handle(self, *args, **options):
        with open(options['csv_file_path']) as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    author, created_a = Author.objects.get_or_create(
                        id = row[2],
                        name = row[1],
                    )

                    _, created_s = Story.objects.get_or_create(
                        id = row[0],
                        title = row[3],
                        pub_date = row[4],
                        summary = row[5],
                        tags = row[6],
                        downloads= row[7],
                        words = row[8],
                        author = author,
                    )