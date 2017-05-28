# Views for our character app

from django.http import Http404
from django.shortcuts import render
from django.conf import settings

from django.template.defaulttags import register
@register.filter
# def get_item(dictionary, key):
#     return dictionary.get(key)
def lookup(dict, index):
    if index in dict:
        return dict[index]
    return ''

from evennia.utils.search import object_search
from evennia.utils.utils import inherits_from
from sr5.data.skills import Skills

def skill_view(request):
    skill_list = Skills.skill_list

    # skill_view_obj = open("mechanics/skill_view.html", "r")
    # skill_view_code = skill_view_obj.read()

    return render(request, 'mechanics/skill_view.html', {'skill_list': skill_list, 'archdesc': Skills.skill_list['archery']['description']})
