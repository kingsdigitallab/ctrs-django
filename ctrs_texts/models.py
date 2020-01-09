from django.db import models
from django.utils.text import slugify
from wagtail.snippets.models import register_snippet
from wagtail.search import index
import re
import lxml.etree as ET
from lxml import etree


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
        ordering = ['name']

    def __str__(self):
        return self.short_name or self.name

    @classmethod
    def get_all(cls):
        '''Returns all instances as a dictionary {slug: instance}'''
        return {
            r.slug: r
            for r
            in cls.objects.all()
        }

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
        xml = get_xml_from_unicode(self.content, ishtml=True, add_root=True)
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

            variants = etree.Element('span')
            variants.attrib['class'] = 'variants'
            region.append(variants)

            for mi, r in enumerate(regions[ri]):

                child = etree.Element('span')
                child.attrib['class'] = 'variant'

                ms = etree.Element('span')
                ms.attrib['class'] = 'ms'
                # ms.text = chr(65 + mi)
                ms.text = members[mi].short_name
                child.append(ms)

                reading = etree.Element('span')
                reading.attrib['class'] = 'reading'
                reading.text = r
                child.append(reading)

                # child.text = r
                variants.append(child)

            ri += 1

        # print(regions)

        ret = get_unicode_from_xml(xml, remove_root=True)

        return ret

    def get_regions(self):
        ret = []

        xml = get_xml_from_unicode(self.content, ishtml=True, add_root=True)

        for region in xml.findall('.//span[@data-dpt-type="unsettled"]'):
            ret.append(get_unicode_from_xml(region, text_only=True))

        return ret

    # IGNORE the warning message from command line about slug
    # not defined in abstracted_text.
    # It is defined via the AbstractNamedModel.
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


def get_xml_from_unicode(document, ishtml=False, add_root=False):
    # document = a unicode object containing the document
    # ishtml = True will be more lenient about the XML format
    #          and won't complain about named entities (&nbsp;)
    # add_root = True to surround the given document string with
    #         <root> element before parsing. In case there is no
    #        single containing element.

    if document and add_root:
        document = r'<root>%s</root>' % document

    parser = None
    if ishtml:
        from io import StringIO
        parser = ET.HTMLParser()
        # we use StringIO otherwise we'll have encoding issues
        d = StringIO(document)
    else:
        from io import BytesIO
        d = BytesIO(document.encode('utf-8'))
    ret = ET.parse(d, parser)

    return ret


def get_unicode_from_xml(xmltree, encoding='utf-8',
                         text_only=False, remove_root=False):
    # if text_only = True => strip all XML tags
    # EXCLUDE the TAIL
    if text_only:
        return get_xml_element_text(xmltree)
    else:
        # import regex as re

        if hasattr(xmltree, 'getroot'):
            xmltree = xmltree.getroot()
        ret = ET.tostring(xmltree, encoding=encoding).decode('utf-8')
        if xmltree.tail is not None and ret[0] == '<':
            # remove the tail
            ret = re.sub(r'[^>]+$', '', ret)

        if remove_root:
            r = [
                ret.find('<root>'),
                ret.rfind('</root>')
            ]
            if r[0] > 0 and r[1] > r[0]:
                ret = ret[r[0] + len('<root>'):r[1]]

        return ret


def get_xml_element_text(element):
    # returns all the text within element and its descendants
    # WITHOUT the TAIL.
    #
    # element is etree Element object
    #
    # '<r>t0<e1>t1<e2>t2</e2>t3</e1>t4</r>'
    # e = (xml.findall(el))[0]
    # e.text => t1
    # e.tail => t4 (! part of e1)
    # get_xml_element_text(element) => 't1t2t3'

    return ''.join(element.itertext())
