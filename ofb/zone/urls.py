from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('stories/', views.StoriesView.as_view(), name='stories'),
    path('stories/<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('author/<int:pk>/', views.DetailAuthorView.as_view(), name='author'),
    path('tags/', views.TagListView.as_view(), name='tags'),
    path('about/', views.AboutView.as_view(), name='about'),
]