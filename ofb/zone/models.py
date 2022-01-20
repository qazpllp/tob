from django.db import models
from django_filters import FilterSet, OrderingFilter

class Tag(models.Model):
    slug = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.slug

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

class StoryFilter(FilterSet):
    o = OrderingFilter(
        fields = (
            ('title', 'title'),
            ('downloads', 'downloads'),
            ('words', 'words'),
            ('pub_date', 'date'),
            ('author__name', 'author')
        )
    )

    class Meta:
        model = Story
        # fields = ['title', 'downloads']
        fields = {
            'title': ['icontains'],
            'downloads': ['exact'],
            # 'tags': ['in'],
            'pub_date': ['range'],
        }
