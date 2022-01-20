from django_filters import FilterSet, OrderingFilter, BaseInFilter, NumberFilter, ModelMultipleChoiceFilter

from .models import Story, Tag

class StoryFilter(FilterSet):
    # Tags multiple choice selection filter
    tags__in = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=True
    )

    # Possibilities to order the results
    o = OrderingFilter(
        fields = (
            ('title', 'title'),
            ('downloads', 'downloads'),
            ('words', 'words'),
            ('author__name', 'author'),
            ('pub_date', 'date'),
        )
    )

    class Meta:
        model = Story
        # Fields to search on
        fields = {
            'title': ['icontains'],
            'downloads': ['lte','gte','exact'],
            'author__name': ['icontains'],
            'pub_date': ['year'],
        }
