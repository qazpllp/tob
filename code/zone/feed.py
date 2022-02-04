from django.contrib.syndication.views import Feed

from .models import Story

class LatestStoriesFeed(Feed):
   title = "The Overflowing Bra Stories"
   link = "/stories/"
   description = "Updates on new stories."

   def items(self):
      return Story.objects.all().order_by("-pub_date")[:10]
		
   def item_title(self, item):
      return item.title
		
   def item_description(self, item):
      return item.summary
		