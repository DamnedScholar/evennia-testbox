"""
Url definition file to redistribute incoming URL requests to django
views. Search the Django documentation for "URL dispatcher" for more
help.

"""
from django.conf.urls import url, include

# default evennia patterns
from evennia.web.urls import urlpatterns

# django-wiki
from wiki.urls import get_pattern as get_wiki_pattern
from django_nyt.urls import get_pattern as get_nyt_pattern

# eventual custom patterns
custom_patterns = [
    url(r'^character/', include('web.character.urls',
                                namespace='character', app_name='character')),
    url(r'^system/', include('sr5.systemview.urls',
                             namespace='character', app_name='system')),
    url(r'^notifications/', get_nyt_pattern()),
    url(r'^wiki/', get_wiki_pattern()),
]

# this is required by Django.
urlpatterns = custom_patterns + urlpatterns
