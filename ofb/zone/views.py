from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator

from .models import Story, Author, Tag

paginate_stories = 10

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
    paginate_by = paginate_stories

    def get_queryset(self):
        """
        Returns the last 5 piblished stories
        """
        return Story.objects.order_by('-pub_date')

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
    model = Tag

class TagDetailView(generic.ListView):
    model = Story
    paginate_by = paginate_stories
    template_name = 'zone/tag_detail.html'

    def get_queryset(self):
        """
        Returns the last 5 piblished stories
        """
        return Story.objects.filter(tags__id = self.kwargs['pk'])
   
class AboutView(generic.ListView):
    template_name = 'zone/about.html'
    model = Story