from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator

from .models import Story, Author, Tag

paginate_stories = 20

class IndexView(generic.TemplateView):
    template_name = 'zone/index.html'

    def get_context_data(self, *args, **kwargs):
        """
        Returns the approxiate number of works and authors
        """
        # pagination
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        context.update({'works': round(len(Story.objects.all()),-1)})
        context.update({'authors': round(len(Author.objects.all()),-1)})
        return context

class StoriesView(generic.ListView):
    context_object_name = 'latest_story_list'
    paginate_by = paginate_stories

    def get_queryset(self):
        """
        Returns the last 5 published stories
        """
        return Story.objects.order_by('-pub_date')

    def get_context_data(self, *args, **kwargs):
        """
        Limit pagination pages when appropriate
        """
        # pagination
        context = super(StoriesView, self).get_context_data(*args, **kwargs)
        context = pagination(context)
        return context

class DetailView(generic.DetailView):
    model = Story

class DetailAuthorView(generic.DetailView):
    model = Author

    def get_context_data(self, *args, **kwargs):
        """
        Get the stories by the author
        """
        context = super(DetailAuthorView, self).get_context_data(*args, **kwargs)
        context["story_list"] = Story.objects.filter(author__id = self.kwargs['pk']).order_by('-pub_date')
        return context

class TagListView(generic.ListView):
    model = Tag

class TagDetailView(generic.ListView):
    model = Story
    paginate_by = paginate_stories
    template_name = 'zone/tag_detail.html'

    def get_queryset(self):
        """
        Returns the published stories with the relevant tag
        """
        return Story.objects.filter(tags__id = self.kwargs['pk']).order_by('-pub_date')

    def get_context_data(self, *args, **kwargs):
        """
        Get the tag detail info, and limit pagination pages when appropriate
        """
        # Tag
        context = super(TagDetailView, self).get_context_data(*args, **kwargs)
        context["tag"] = Tag.objects.get(pk = self.kwargs['pk'])

        # pagination
        context = pagination(context)
        return context

class AboutView(generic.ListView):
    template_name = 'zone/about.html'
    model = Story

def pagination(context, pages_either_side=5):
    """
    Limit the number of pages shown.
    Show this page, and +-pages_either_side total, at most
    https://stackoverflow.com/a/39090909
    """
    if not context.get('is_paginated', False):
        return context

    paginator = context.get('paginator')
    num_pages = paginator.num_pages
    current_page = context.get('page_obj')
    page_no = current_page.number

    if num_pages <= (pages_either_side*2+1) or page_no <= pages_either_side+1:  # case 1 and 2
        pages = [x for x in range(1, min(num_pages + 1, (pages_either_side*2+2)))]
    elif page_no > num_pages - (pages_either_side+1):  # case 4
        pages = [x for x in range(num_pages - (pages_either_side*2), num_pages + 1)]
    else:  # case 3
        pages = [x for x in range(page_no - pages_either_side, page_no + pages_either_side+1)]

    context.update({'pages': pages})
    return context