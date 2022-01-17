from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    id = models.IntegerField(primary_key=True)

class Story(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date published')
    summary = models.CharField(max_length=500)
    downloads = models.IntegerField()
    words = models.IntegerField()
    id = models.IntegerField(primary_key=True)