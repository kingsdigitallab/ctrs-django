from django.db import models
from django.utils.text import slugify
from wagtail.snippets.models import register_snippet
from wagtail.search import index
from .models_abstract import ImportedModel, TimestampedModel, NamedModel
from . import utils


class EncodedTextStatus(NamedModel):
    sort_order = models.IntegerField(
        blank=False, null=False, default=0,
        help_text='The order of this status in your workflow.'
    )

    class Meta:
        verbose_name = 'Text Status'
        verbose_name_plural = 'Text Statuses'


class EncodedTextType(NamedModel):
    pass


@register_snippet
class EncodedText(index.Indexed, TimestampedModel, ImportedModel):
    '''
    An XML-encoded text.
    '''
    # e.g. draft, to-be-reviewed, live
    status = models.ForeignKey(
        'EncodedTextStatus', blank=True, null=True,
        related_name='encoded_texts',
        on_delete=models.SET_NULL
    )
    # e.g. translation or transcription
    type = models.ForeignKey(
        'EncodedTextType', blank=True, null=True,
        related_name='encoded_texts',
        on_delete=models.SET_NULL
    )
    # The XML content
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

    def content_variants(self):
        ret = self.content

        ab_text = self.abstracted_text
        members = list(ab_text.members.all())
        if not members:
            return ret

        regions = []
        for mi, member in enumerate(members):
            other_content = member.encoded_texts.filter(type=self.type).first()
            if not other_content:
                continue
            for ri, region in enumerate(other_content.get_regions()):
                if len(regions) <= ri:
                    regions.append(['?'] * len(members))
                regions[ri][mi] = region

        #
        xml = utils.get_xml_from_unicode(
            self.content, ishtml=True, add_root=True)
        ri = 0
        for region in xml.findall('.//span[@data-dpt-type="unsettled"]'):
            # _Element
            if ri >= len(regions):
                break
            tail = region.tail
            attribs = {k: v for k, v in region.attrib.items()}
            region.clear()
            for k, v in attribs.items():
                region.attrib[k] = v
            region.tail = tail
            # region.text = ' | '.join('<span>{}</span>'.format(regions[ri]))

            variants = utils.append_xml_element(
                region, 'span', None, class_='variants'
            )

            for mi, r in enumerate(regions[ri]):

                variant = utils.append_xml_element(
                    variants, 'span', None, class_='variant'
                )

                utils.append_xml_element(
                    variant, 'span', members[mi].short_name,
                    class_='ms'
                )

                utils.append_xml_element(
                    variant, 'span', r,
                    class_='reading'
                )

            ri += 1

        # print(regions)

        ret = utils.get_unicode_from_xml(xml, remove_root=True)

        return ret

    def get_regions(self):
        ret = []

        xml = utils.get_xml_from_unicode(
            self.content, ishtml=True, add_root=True)

        for region in xml.findall('.//span[@data-dpt-type="unsettled"]'):
            ret.append(utils.get_unicode_from_xml(region, text_only=True))

        return ret

    # IGNORE the warning message from command line about slug
    # not defined in abstracted_text.
    # It is defined via the NamedModel.
    search_fields = [
        index.SearchField('abstracted_text__slug', partial_match=True),
    ]


@register_snippet
class Repository(NamedModel, ImportedModel):
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
class Manuscript(TimestampedModel, ImportedModel):
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


class AbstractedTextType(NamedModel):

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
class AbstractedText(NamedModel, ImportedModel):
    '''
    A Text: either a MS Text, a Version Text or a Work Text
    '''
    # E.g. manuscript, version, work
    type = models.ForeignKey(
        'AbstractedTextType', blank=True, null=True,
        related_name='abstracted_texts',
        on_delete=models.SET_NULL
    )
    # Optional link to the 'parent'
    group = models.ForeignKey(
        'self', blank=True, null=True,
        related_name='members',
        on_delete=models.SET_NULL
    )

    def get_status(self):
        ret = None
        transc = self.encoded_texts.filter(
            type__slug='transcription').only('status').first()
        if transc:
            ret = transc.status
        return ret

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

    def full_name_with_siglum(self):
        ret = format(self.name)
        ms_text = self.manuscript_texts.first()
        if ms_text:
            ret = ms_text.manuscript.repository.city + ', ' + ret
        if self.short_name:
            ret = self.short_name + ': ' + ret
        return ret


class ManuscriptText(models.Model):
    '''
    Essentially a m2m relationship
    between a Manuscript and the Texts it contains.

    TODO: convert to 12m => move manuscript & locus fields to abstracted_text
    '''
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
    # the folio/page range for that text in the manuscript
    locus = models.CharField(max_length=200, null=True, blank=True)

    @classmethod
    def update_or_create(cls, manuscript, locus):
        rec, created = cls.objects.update_or_create(
            manuscript=manuscript, locus=locus,
        )

        return rec, created

    def __str__(self):
        return '{}, {}'.format(self.manuscript, self.locus)
