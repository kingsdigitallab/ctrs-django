from __future__ import unicode_literals

from django import forms
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.core.blocks import (
    CharBlock, FieldBlock, PageChooserBlock, RawHTMLBlock, RichTextBlock,
    StreamBlock, StructBlock, TextBlock, URLBlock
)
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class HTMLAlignmentChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('default', 'Default'), ('full', 'Full width'),
    ))


class AlignedHTMLBlock(StructBlock):
    html = RawHTMLBlock()
    alignment = HTMLAlignmentChoiceBlock()


class IconChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('external-link-square', 'External link'),
        ('book', 'Declaration of Arbroath'),
        ('video', 'Video'),
        ('image', 'Images'),
        ('gavel', 'Robert I\'s Law'),
        ('file-alt', 'Regiam Majestatem'),
        ('pencil-podcast', 'Blog and podcasts'),
        ('pencil', 'Blog'),
        ('podcast', 'Podcast'),
        ('newspaper', 'New sources'),
        ('graduation-cap', 'Resources for teachers')
    ))


class HomePageBlock(StructBlock):
    url = URLBlock(required=False)
    page = PageChooserBlock(required=False)
    title = CharBlock()
    image = ImageChooserBlock()
    description = TextBlock()
    icon = IconChoiceBlock()

    class Meta:
        template = 'cms/blocks/home_page_block.html'
        help_text = '''
        Use either URL or page, if both are filled in URL takes precedence.
        For an email button, use the format mailto:email@address.com'''


class ImageFormatChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('left', 'Wrap left'), ('right', 'Wrap right'),
        ('mid', 'Mid width'), ('full-width', 'Full width'),
    ))


class ImageBlock(StructBlock):
    image = ImageChooserBlock()
    caption = RichTextBlock()
    alignment = ImageFormatChoiceBlock()
    text = RichTextBlock(required=False)

    class Meta:
        template = 'cms/blocks/image_block.html'


class LinkStyleChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('default', 'Default'), ('button', 'Button'),
    ))


class LinkBlock(StructBlock):
    url = CharBlock(required=False)
    page = PageChooserBlock(required=False)
    label = CharBlock()
    style = LinkStyleChoiceBlock()

    class Meta:
        help_text = '''
        Use either URL or page, if both are filled in URL takes precedence.'''
        template = 'cms/blocks/link_block.html'


class PullQuoteStyleChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('default', 'Default'), ('with-background', 'With background image'),
    ))


class PullQuoteBlock(StructBlock):
    quote = TextBlock('quote title')
    attribution = CharBlock()
    affiliation = CharBlock(required=False)
    style = PullQuoteStyleChoiceBlock()

    class Meta:
        template = 'cms/blocks/pull_quote_block.html'


class CMSStreamBlock(StreamBlock):
    # home = HomePageBlock(icon='grip', label='Homepage Block')

    h2 = CharBlock(icon='title', classname='title')
    h3 = CharBlock(icon='title', classname='title')
    h4 = CharBlock(icon='title', classname='title')
    h5 = CharBlock(icon='title', classname='title')

    home_page_block = HomePageBlock(icon='placeholder')
    intro = RichTextBlock(icon='pilcrow')
    paragraph = RichTextBlock(icon='pilcrow')
    pullquote = PullQuoteBlock(icon='openquote')

    image = ImageBlock(label='Aligned image and text', icon='image')
    document = DocumentChooserBlock(icon='doc-full-inverse')
    link = LinkBlock(icon='link')
    embed = EmbedBlock(icon='media')

    html = AlignedHTMLBlock(icon='code', label='Raw HTML')

    table = TableBlock(icon='table', label='Table')
