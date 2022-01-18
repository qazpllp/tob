from django.contrib import admin

from .models import Author, Story, Tag

admin.site.register(Author)
admin.site.register(Story)
admin.site.register(Tag)