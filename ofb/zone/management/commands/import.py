import csv
import ast
from turtle import title
from django.core.management import BaseCommand
from zone.models import Author, Story, Tag

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

                    tag_array = ast.literal_eval(row[6])
                    tags = []
                    for t in tag_array:
                        tag, created_t = Tag.objects.get_or_create(
                            slug = t
                        )
                        tags.append(tag)


                        tag, created_t = Tag.objects.update_or_create(
                            slug = row[0],
                            defaults = {'description': row[1]}
                        )

                    story, created_s = Story.objects.update_or_create(
                        id = row[0],
                        title = row[3],
                        pub_date = row[4],
                        summary = row[5],
                        author = author,
                        defaults = {
                            'words': row[8],
                            'downloads': row[7],
                        }
                    )

                    # story must be saved before assigning many-to-many tags field
                    for t in tags:
                        story.tags.add(t)
