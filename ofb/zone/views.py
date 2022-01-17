from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Story, Author

class IndexView(generic.ListView):
    context_object_name = 'latest_story_list'

    def get_queryset(self):
        """
        Returns the last 5 piblished stories
        """
        return Story.objects.order_by('-pub_date')[:5]

class DetailView(generic.DetailView):
    model = Story

class DetailAuthorView(generic.DetailView):
    model = Author
