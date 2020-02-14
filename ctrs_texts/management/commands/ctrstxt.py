from django.core.management.base import BaseCommand
from ctrs_texts.models import (
    Repository, Manuscript, AbstractedText, EncodedText,
    AbstractedTextType, EncodedTextStatus
)
from django.utils.text import slugify
from ctrs_texts.utils import get_xml_from_unicode, get_unicode_from_xml


class Command(BaseCommand):
    help = 'CTRS text management toolbox'

    def log(self, message, verbosity=1):
        if verbosity <= self.get_verbosity():
            self.stdout.write(message)

    def error(self, message):
        self.stderr.write(self.style.ERROR(message))

    def get_verbosity(self):
        return self.verbosity

    def add_arguments(self, parser):
        parser.add_argument('action', nargs='?', type=str)
        parser.add_argument('options', nargs='*', type=str)

    def handle(self, *args, **options):
        action = options['action']
        self.options = options['options']
        self.verbosity = options['verbosity']

        valid = False

        if action == 'import':
            valid = self.handle_import()

        if action == 'delete':
            for m in [
                Repository, Manuscript,
                AbstractedText, EncodedText, AbstractedTextType,
                EncodedTextStatus
            ]:
                m.objects.all().delete()
            valid = True

        if not valid:
            self.show_help()
        else:
            self.log('done')

    def handle_import(self):
        '''
        curl
        "http://localhost:8001/digipal/api/textcontentxml/?@select=*status,id,str,content,*text_content,*item_part,group,group_locus,type,*current_item,locus,shelfmark,*repository,place&@limit=1000"
        > arch-content.json
        '''
        ret = False

        if len(self.options) != 1:
            return ret

        ret = True

        file_path = self.options.pop(0)
        self.action_import(file_path)

        return ret

    def action_import(self, input_file):
        data = None

        import json
        try:
            with open(input_file, 'rt') as fh:
                data = json.load(fh)
        except Exception as e:
            self.error('%s' % e)
            return False

        return self.import_json(data)

    def import_json(self, data):
        '''
        Imports the text XML and metadata
        from a json file exported from Archetype.

        Insert or update.
        Stores archetype record id in .imported_id field
        to permanently keep track of the mapping.
        '''
        ab_types = AbstractedTextType.get_or_create_default_types()
        statuses = {}
        # see delete_unimported_records()
        models_imported_ids = {m: [] for m in [
            Repository, Manuscript, AbstractedText, EncodedText
        ]}

        # mapping from itempart id to abstracted text id
        arch_ipid_to_ab_txt = {}

        for jtcxml in data['results']:
            self.log(jtcxml['str'], 2)
            jtc = jtcxml['text_content']
            jip = jtc['item_part']
            jci = jip['current_item']
            jrepo = jci['repository']

            if jip['type'] is None:
                continue
            ip_type = slugify(jip['type'])

            status_name = jtcxml['status']['str']
            status_slug = slugify(status_name)
            status = statuses.get(status_slug, None)
            if status is None:
                status, _ = EncodedTextStatus.objects.get_or_create(
                    slug=status_slug,
                    defaults={'name': status_name}
                )
                statuses[status_slug] = status

            if ip_type in ['manuscript']:
                repo, _ = Repository.update_or_create(
                    jrepo['id'], jrepo['place'], jrepo['str']
                )
                models_imported_ids[Repository].append(jrepo['id'])
                ms, _ = Manuscript.update_or_create(
                    jci['id'], repo, jci['shelfmark']
                )
                models_imported_ids[Manuscript].append(jci['id'])
                ab_txt, _ = AbstractedText.update_or_create(
                    jip['id'], ab_types[ip_type],
                    manuscript=ms, locus=jip['locus']
                )
                models_imported_ids[AbstractedText].append(jip['id'])
            else:
                ab_txt, _ = AbstractedText.update_or_create(
                    jip['id'], ab_types[ip_type],
                    name=jip['str'],
                )
                models_imported_ids[AbstractedText].append(jip['id'])

            EncodedText.update_or_create(
                jtc['id'], ab_txt, jtc['type'],
                self.clean_archetype_text_content(jtcxml['content']),
                status
            )
            models_imported_ids[EncodedText].append(jtc['id'])

            arch_ipid_to_ab_txt[jip['id']] = ab_txt

        # relationship among the abstracted texts
        # ms-text -> version-text -> work-text
        for jtcxml in data['results']:
            jtc = jtcxml['text_content']
            jip = jtc['item_part']
            ab_text = arch_ipid_to_ab_txt.get(jip['id'], None)
            if ab_text:
                ab_text_group = arch_ipid_to_ab_txt.get(
                    jip.get('group__id', None), None
                )
                ab_text.group = ab_text_group
                ab_text.short_name = jip.get('group_locus', None)
                ab_text.save()

        deleted_count = self.delete_unimported_records(models_imported_ids)

        self.log('{} inserted/updated, {} deleted.'.format(
            sum([len(ids) for m, ids in models_imported_ids.items()]),
            deleted_count
        ))

        return True

    def clean_archetype_text_content(self, content):
        # non-breaking spaces -> normal spaces
        ret = (content or '').replace('&nbsp;', '').replace('\xA0', ' ')

        # allow the empty symbol to be styled
        if 0:
            # ac-128: disabled until confirmed unnecessary
            ret = ret.replace('∅', '<span class="no-text">∅</span>')

        # ac-128: add an empty-region class the spans that only contains an
        # empty symbol
        import re
        ret = re.sub(
            r'(<span[^>]+data-dpt-type="unsettled"[^>]*)(>\s*∅\s*</span>)',
            r'\1 class="empty-region"\2',
            ret
        )

        # Minor XML transforms
        xml = get_xml_from_unicode(ret, ishtml=True, add_root=True)

        for region in xml.findall('.//span[@data-dpt-type="unsettled"]'):
            # add data-dpt-group="version" to the v-regions
            if not region.attrib.get('data-dpt-group', None):
                region.attrib['data-dpt-group'] = 'version'

        ret = get_unicode_from_xml(xml, remove_root=True)

        return ret

    def delete_unimported_records(self, models_imported_ids):
        '''
        Delete all the records with .imported_id <> None
        which have not been imported by the import command.

        models_imported_ids is a dictionary of the form
        {ModelClass: [id1, id2, ...], }

        returns number of deleted records.
        '''
        ret = 0

        for m, ids in models_imported_ids.items():
            res = m.objects.exclude(imported_id__in=ids).delete()
            if res[0]:
                self.log('Deleted {} {}'.format(res[0], m), 2)
                ret += res[0]

        return ret

    def show_help(self):
        self.stdout.write('''{}

Usage: ACTION OPTIONS

ACTION:

  help
    show this help.

  import FILE
    import all the text content and metadata from FILE.
    update if the record already exists.
    FILE: a json file obtained from archetype API,
          see inline comment (handle_import)
  delete
    delete all the text concent records from the DB

'''.format(self.help))
