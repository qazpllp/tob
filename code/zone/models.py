from django.db import models
from django.urls import reverse

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
    pub_date = models.DateField('date published', max_length=100)
    summary = models.CharField(max_length=2000)
    downloads = models.IntegerField()
    words = models.IntegerField()
    id = models.IntegerField(primary_key=True)
    text = models.TextField()
    tags = models.ManyToManyField(Tag)

    class Meta:
        verbose_name_plural = "stories"
        ordering = ['-pub_date']

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('story-detail', kwargs={'pk': self.pk})