from django.urls import path

from . import views, feed

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # path('stories/', views.StoriesView.as_view(), name='stories'),
    path('stories/<int:pk>/', views.DetailView.as_view(), name='story-detail'),
    path('author/<int:pk>/', views.DetailAuthorView.as_view(), name='author'),
    path('tags/', views.TagListView.as_view(), name='tags'),
    path('tags/<int:pk>/', views.TagDetailView.as_view(), name='tag'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('stories/', views.StoryFilterView.as_view(), name='stories'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('stories/feed', feed.LatestStoriesFeed(), name='story-feed'),
]
