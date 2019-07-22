from django.db import models
from django.utils.text import slugify
from wagtail.snippets.models import register_snippet
from wagtail.search import index


class TimestampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class AbstractNamedModel(index.Indexed, TimestampedModel):
    name = models.CharField(max_length=200, null=False, blank=False)
    short_name = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=200, null=False,
                            blank=False, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.short_name or self.name

    search_fields = [
        index.SearchField('name', partial_match=True),
    ]


class EncodedTextStatus(AbstractNamedModel):
    sort_order = models.IntegerField(
        blank=False, null=False, default=0,
        help_text='The order of this status in your workflow.'
    )

    class Meta:
        verbose_name = 'Text Status'
        verbose_name_plural = 'Text Statuses'


class EncodedTextType(AbstractNamedModel):
    pass


@register_snippet
class EncodedText(index.Indexed, TimestampedModel):
    status = models.ForeignKey(
        'EncodedTextStatus', blank=True, null=True,
        related_name='encoded_texts',
        on_delete=models.SET_NULL
    )
    type = models.ForeignKey(
        'EncodedTextType', blank=True, null=True,
        related_name='encoded_texts',
        on_delete=models.SET_NULL
    )
    content = models.TextField(blank=True, null=True)
    abstracted_text = models.ForeignKey(
        'AbstractedText', blank=False, null=False,
        related_name='encoded_texts',
        on_delete=models.CASCADE
    )

    @classmethod
    def update_or_create(cls, abstracted_text, type_name, content, status):
        encoded_type, _ = EncodedTextType.objects.get_or_create(
            slug=slugify(type_name),
            defaults={'name': type_name}
        )

        rec, created = cls.objects.update_or_create(
            abstracted_text=abstracted_text,
            type=encoded_type,
            defaults={'content': content, 'status': status}
        )

        return rec, created

    def __str__(self):
        return '{} - {} [{}]'.format(
            self.abstracted_text, self.type, self.status
        )

    search_fields = [
        index.SearchField('abstracted_text__slug', partial_match=True),
    ]


@register_snippet
class Repository(AbstractNamedModel):
    city = models.CharField(max_length=200, null=False, blank=False)

    @classmethod
    def update_or_create(cls, place, name):
        rec, created = cls.objects.update_or_create(
            city=place, name=name,
            defaults={'slug': slugify('{}-{}'.format(place, name))}
        )

        return rec, created

    class Meta:
        verbose_name_plural = 'Repositories'


@register_snippet
class Manuscript(TimestampedModel):
    repository = models.ForeignKey(
        'Repository', blank=True, null=True,
        related_name='manuscripts',
        on_delete=models.SET_NULL
    )
    shelfmark = models.CharField(max_length=200, null=True, blank=True)

    @classmethod
    def update_or_create(cls, repository, shelfmark):
        rec, created = cls.objects.update_or_create(
            repository=repository, shelfmark=shelfmark,
        )

        return rec, created

    def __str__(self):
        return '{}, {}'.format(self.repository, self.shelfmark)


class AbstractedTextType(AbstractNamedModel):

    @classmethod
    def get_or_create_default_types(cls):
        return {
            slugify(t): cls.objects.get_or_create(
                name=t, slug=slugify(t)
            )[0]
            for t
            in ['Manuscript', 'Version', 'Work']
        }


@register_snippet
class AbstractedText(AbstractNamedModel):
    type = models.ForeignKey(
        'AbstractedTextType', blank=True, null=True,
        related_name='abstracted_texts',
        on_delete=models.SET_NULL
    )
    group = models.ForeignKey(
        'self', blank=True, null=True,
        related_name='members',
        on_delete=models.SET_NULL
    )

    @classmethod
    def update_or_create(cls, manuscript_text=None, type=None, name=None):
        rec = None
        created = False

        assert manuscript_text or name

        if manuscript_text:
            rec = manuscript_text.abstracted_text
            if rec is None:
                created = True
                rec = cls()
            if name is None:
                name = str(manuscript_text)
            rec.name = name
            rec.type = type
            rec.slug = slugify(str(rec))
            rec.save()
        else:
            rec, created = cls.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    'name': name,
                    'type': type
                }
            )

        if manuscript_text:
            manuscript_text.abstracted_text = rec
            manuscript_text.save()

        return rec, created

    def __str__(self):
        return '{} ({})'.format(self.name, self.type)


class ManuscriptText(models.Model):
    manuscript = models.ForeignKey(
        'Manuscript', blank=True, null=True,
        related_name='manuscript_texts',
        on_delete=models.SET_NULL
    )
    abstracted_text = models.ForeignKey(
        'AbstractedText', blank=True, null=True,
        related_name='manuscript_texts',
        on_delete=models.SET_NULL
    )
    locus = models.CharField(max_length=200, null=True, blank=True)

    @classmethod
    def update_or_create(cls, manuscript, locus):
        rec, created = cls.objects.update_or_create(
            manuscript=manuscript, locus=locus,
        )

        return rec, created

    def __str__(self):
        return '{}, {}'.format(self.manuscript, self.locus)
