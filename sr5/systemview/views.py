# Views for our character app

from django.http import Http404
from django.shortcuts import render
from django.conf import settings

from evennia.utils.search import object_search
from evennia.utils.utils import inherits_from
from sr5.data.skills import Skills

def skill_view(request):
    # Templates can have difficulty displaying complex data structures. Use this function if the information needs to be simplified so that it can be easily digested.

    return render(request, 'mechanics/skill_view.html',
                  {'skill_list': Skills.active,
                   'skill_categories': Skills.categories,
                   'skill_groups': Skills.groups,
                   'skill_attr': Skills.attr}
                 )
