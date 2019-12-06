from __future__ import unicode_literals

import logging

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.shortcuts import render
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.contrib.routable_page.models import route
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel

from .behaviours import WithFeedImage, WithStreamField
from django import forms
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def _paginate(request, items):
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(items, settings.ITEMS_PER_PAGE)

    try:
        items = paginator.page(page)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        items = paginator.page(1)

    return items


class HomePage(Page, WithStreamField):
    subpage_types = [
        'BlogIndexPage',
        'IndexPage',
        'PeopleIndexPage',
        'RichTextPage'
    ]


HomePage.content_panels = [
    FieldPanel('title', classname='full title'),
    StreamFieldPanel('body'),
]

HomePage.promote_panels = Page.promote_panels


class IndexPage(Page, WithStreamField):
    subpage_types = ['IndexPage', 'RichTextPage']


IndexPage.content_panels = [
    FieldPanel('title', classname='full title'),
    StreamFieldPanel('body'),
]

IndexPage.promote_panels = Page.promote_panels


class BlogIndexPage(Page, WithStreamField):
    subpage_types = ['BlogPost']

    @property
    def posts(self):
        # gets list of live blog posts that are descendants of this page
        posts = BlogPost.objects.live().descendant_of(self)

        # orders by most recent date first
        posts = posts.order_by('-date')

        return posts

    @route(r'^$')
    def all_posts(self, request):
        posts = self.posts
        logger.debug('Posts: {}'.format(posts))

        return render(request, self.get_template(request),
                      {'self': self, 'posts': _paginate(request, posts)})

    @route(r'^author/(?P<author>[\w ]+)/$')
    def author(self, request, author=None):
        if not author:
            # Invalid author filter
            logger.error('Invalid author filter')
            return self.all_posts(request)

        posts = self.posts.filter(owner__username=author)

        return render(
            request, self.get_template(request), {
                'self': self, 'posts': _paginate(request, posts),
                'filter_type': 'author', 'filter': author
            }
        )

    @route(r'^tag/(?P<tag>[\w\- ]+)/$')
    def tag(self, request, tag=None):
        if not tag:
            # Invalid tag filter
            logger.error('Invalid tag filter')
            return self.all_posts(request)

        posts = self.posts.filter(tags__name=tag)

        return render(
            request, self.get_template(request), {
                'self': self, 'posts': _paginate(request, posts),
                'filter_type': 'tag', 'filter': tag
            }
        )


BlogIndexPage.content_panels = [
    FieldPanel('title', classname='full title'),
    StreamFieldPanel('body')
]

BlogIndexPage.promote_panels = Page.promote_panels


class PeopleIndexPage(Page, WithFeedImage, WithStreamField):
    subpage_types = ['IndexPage', 'PeoplePage', 'RichTextPage']


PeopleIndexPage.content_panels = [
    FieldPanel('title', classname='full title'),
    StreamFieldPanel('body')
]

PeopleIndexPage.promote_panels = Page.promote_panels


class PeoplePage(Page, WithFeedImage, WithStreamField):
    subpage_types = []

    job_title = models.CharField(max_length=255)


PeoplePage.content_panels = [
    FieldPanel('title', classname='full title'),
    FieldPanel('job_title'),
    StreamFieldPanel('body')
]

PeoplePage.promote_panels = Page.promote_panels + [
    ImageChooserPanel('feed_image')
]


class RichTextPage(Page, WithFeedImage, WithStreamField):
    subpage_types = []


RichTextPage.content_panels = [
    FieldPanel('title', classname='full title'),
    StreamFieldPanel('body'),
]

RichTextPage.promote_panels = Page.promote_panels + [
    ImageChooserPanel('feed_image')
]


class BlogPostTag(TaggedItemBase):
    content_object = ParentalKey('BlogPost', related_name='tagged_items')


class BlogPost(Page, WithFeedImage, WithStreamField):
    tags = ClusterTaggableManager(through=BlogPostTag, blank=True)
    date = models.DateField('Post date')

    authors = ParentalManyToManyField(
        User,
        verbose_name='authors',
        blank=True,
        editable=True,
        related_name='authored_blogposts',
        # help_text=''
    )

    subpage_types = []

    def get_authors(self):
        ret = self.authors.all()
        if not ret:
            ret = []
            if self.owner:
                ret.append(self.owner)
        return ret

    @property
    def blog_index(self):
        # finds closest ancestor which is a blog index
        return self.get_ancestors().type(BlogIndexPage).last()

    content_panels = [
        FieldPanel('title', classname='full title'),
        FieldPanel('date'),
        StreamFieldPanel('body')
    ]

    promote_panels = Page.promote_panels + [
        ImageChooserPanel('feed_image'),
        FieldPanel('authors', widget=forms.CheckboxSelectMultiple),
        FieldPanel('tags'),
    ]
