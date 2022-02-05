from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

from .models import Story

class StaticViewSitemap(Sitemap):
    def items(self):
        return ['index', 'about']
    def location(self, item):
        return reverse(item)

class StoriesSitemap(Sitemap):
    changefreq = "never"

    def items(self):
        return Story.objects.all()
    
    def lastmod(self, obj):
        return obj.pub_date