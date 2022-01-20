from django.db import models
from django import forms
from django.forms import ModelForm
import django_filters

from .models import Story

class StoryFilter(django_filters.FilterSet):
    words__gt = django_filters.NumberFilter(field_name='words', lookup_expr='gt')

    class Meta:
        model = Story
        fields = {
            'downloads': ['lt', 'gt'],
            'pub_date': ['exact', 'year__gt'],
        }
        # filter_overrides = {
        #     models.CharField: {
        #         'filter_class': django_filters.CharFilter,
        #         'extra': lambda f: {
        #             'lookup_expr': 'icontains',
        #         },
        #     },
        # }

class StoryForm(ModelForm):
    class Meta:
        model = Story
        fields = ['title', 'words']
