from django.forms import CheckboxSelectMultiple
from django_filters import FilterSet, OrderingFilter
from django.db import models
from django import forms

import django_filters
from crispy_forms.helper import FormHelper

from .models import Story, Tag

class StoryFilter(FilterSet):
    # Tags multiple choice selection filter
    story__tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=True,
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
            'pub_date': ['year'],
        }
        filter_overrides = {
            models.ManyToManyField: {
                'filter_class':  django_filters.ModelMultipleChoiceFilter,
                'extra': lambda f: {
                    'widget': forms.CheckboxSelectMultiple
                }
            }
        }

    @property                                                                                        
    def form(self):                                                                                  
       self._form = super(StoryFilter, self).form                                                     
       self._form.helper = FormHelper()                                                              
       self._form.helper.form_tag = False                                                            
       self._form.helper.form_style = 'inline'                                                       
       return self._form 