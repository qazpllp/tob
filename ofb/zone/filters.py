from django.forms import CheckboxSelectMultiple
from django_filters import FilterSet, OrderingFilter
from django.db import models
from django import forms

import django_filters

from .models import Story, Tag

# Unique years
year_choices = ()
for c in Story.objects.dates('pub_date', 'year').reverse():
    year_choices = year_choices + ((c.year, str(c.year)),)

class StoryFilter(FilterSet):
    # Tags multiple choice selection filter
    story__tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=True,
    )

    # Have only the years within the database selectable
    pub_date__year = django_filters.ChoiceFilter(
        choices = year_choices
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
        # Fields to filter on
        fields = {
            'title': ['icontains'],
            'downloads': ['lte','gte','exact'],
            'author__name': ['icontains'],
            # 'pub_date': ['year'],
        }