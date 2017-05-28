from django.template.defaulttags import register
@register.filter(name="lookup")
# def get_item(dictionary, key):
#     return dictionary.get(key)
def lookup(dict, index1, index2):
    if index in dict:
        return dict[index][index]
    return ''
