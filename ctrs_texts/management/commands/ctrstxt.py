from django.core.management.base import BaseCommand
from ctrs_texts.models import (
    Repository, Manuscript, AbstractedText, EncodedText,
    AbstractedTextType, EncodedTextStatus
)
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'CTRS text management toolbox'

    @classmethod
    def log(cls, message):
        print(message)

    @classmethod
    def error(cls, message):
        cls.log('ERROR: ' + message)

    def add_arguments(self, parser):
        parser.add_argument('action', nargs='?', type=str)
        parser.add_argument('options', nargs='*', type=str)

    def handle(self, *args, **options):
        action = options['action']
        self.options = options['options']

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

    @classmethod
    def action_import(cls, input_file):
        data = None

        import json
        try:
            with open(input_file, 'rt') as fh:
                data = json.load(fh)
        except Exception as e:
            cls.error('%s' % e)
            return False

        return cls.import_json(data)

    @classmethod
    def import_json(cls, data):
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
            print(jtcxml['str'])
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

            # clean the input text
            content = (jtcxml['content'] or '').replace(
                '&nbsp;', '').replace('\xA0', ' ')

            EncodedText.update_or_create(
                jtc['id'], ab_txt, jtc['type'], content, status
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

        cls.delete_unimported_records(models_imported_ids)

        return True

    @classmethod
    def delete_unimported_records(cls, models_imported_ids):
        '''
        Delete all the records with .imported_id <> None
        which have not been imported by the import command.

        models_imported_ids is a dictionary of the form
        {ModelClass: [id1, id2, ...], }
        '''
        for m, ids in models_imported_ids.items():
            res = m.objects.exclude(imported_id__in=ids).delete()
            if res[0]:
                print('Deleted {} {}'.format(res[0], m))

    def show_help(self):
        print('''ACTION OPTIONS

{}

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
