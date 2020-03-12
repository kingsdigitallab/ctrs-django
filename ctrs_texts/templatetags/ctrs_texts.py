from django import template
from ..models import AbstractedText

register = template.Library()


@register.inclusion_tag('ctrs_texts/text_list.html')
def text_list(work_slug=None):
    works = AbstractedText.objects.filter(
        type__slug='work',
    )
    if work_slug and work_slug.lower() != 'all':
        works = works.filter(slug=work_slug)
    ret = {
        'works': works,
    }
    return ret
