from django.db import models

class Tag(models.Model):
    slug = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.description

class Author(models.Model):
    name = models.CharField(max_length=100)
    id = models.IntegerField(primary_key=True)

    def __str__(self):
        return self.name

class Story(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date published')
    summary = models.CharField(max_length=500)
    downloads = models.IntegerField()
    words = models.IntegerField()
    id = models.IntegerField(primary_key=True)
    tags = models.ManyToManyField(Tag)

    class Meta:
        verbose_name_plural = "stories"

    def __str__(self):
        return self.title

