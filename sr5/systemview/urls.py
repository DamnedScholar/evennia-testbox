# URL patterns for the character app

from django.conf.urls import url
from sr5.systemview.views import skill_view

urlpatterns = [
    url(r'^skills', skill_view, name="skill_view")
]
