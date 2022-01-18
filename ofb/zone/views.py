from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Story, Author

class IndexView(generic.ListView):
    template_name = 'zone/index.html'
    context_object_name = 'latest_story_list'

    def get_queryset(self):
        """
        Returns the last 5 piblished stories
        """
        return Story.objects.order_by('-pub_date')[:5]

class StoriesView(generic.ListView):
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

    def get_context_data(self, *args, **kwargs):
        """
        Get the stories by the author
        """
        context = super(DetailAuthorView, self).get_context_data(*args, **kwargs)
        context["story_list"] = Story.objects.filter(author__id = self.kwargs['pk'])
        return context

class TagListView(generic.ListView):
    template_name = 'zone/tags.html'
    model = Story

class AboutView(generic.ListView):
    template_name = 'zone/about.html'
    model = Story