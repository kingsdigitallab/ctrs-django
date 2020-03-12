from django.db import models
from wagtail.search import index


class ImportedModel(models.Model):
    # The id of the record in Archetype.
    # So existing records are not imported twice, but updated instead.
    imported_id = models.IntegerField(blank=True, null=True)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class NamedModel(index.Indexed, TimestampedModel):
    name = models.CharField(max_length=200, null=False, blank=False)
    short_name = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=200, null=False,
                            blank=False, unique=True)

    class Meta:
        abstract = True
        ordering = ['short_name', 'name']

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
