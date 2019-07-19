from django.core.management.base import BaseCommand
from ctrs_texts.models import Repository, Manuscript, ManuscriptText,\
    AbstractedText, EncodedText, AbstractedTextType, EncodedTextStatus
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

        if not valid:
            self.show_help()
        else:
            self.log('done')

    def handle_import(self):
        '''
        http://localhost:8001/digipal/api/textcontentxml/?@select=*status,id,str,content,*text_content,*item_part,*text,type,*current_item,locus,shelfmark,*repository,place
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
        ab_types = AbstractedTextType.get_or_create_default_types()
        statuses = {}

        for jtcxml in data['results']:
            print(jtcxml['str'])
            jtc = jtcxml['text_content']
            jip = jtc['item_part']
            jci = jip['current_item']
            jrepo = jci['repository']

            status_name = jtcxml['status']['str']
            status_slug = slugify(status_name)
            status = statuses.get(status_slug, None)
            if status is None:
                status, _ = EncodedTextStatus.objects.get_or_create(
                    slug=status_slug,
                    defaults={'name': status_name}
                )
                statuses[status_slug] = status

            repo, _ = Repository.update_or_create(jrepo['place'], jrepo['str'])
            ms, _ = Manuscript.update_or_create(repo, jci['shelfmark'])
            ms_txt, _ = ManuscriptText.update_or_create(ms, jip['locus'])
            ab_txt, _ = AbstractedText.update_or_create(
                manuscript_text=ms_txt, type=ab_types['manuscript']
            )
            en_txt, _ = EncodedText.update_or_create(
                ab_txt, jtc['type'], jtcxml['content'], status
            )

            # version

        return True

    def show_help(self):
        print('''ACTION OPTIONS

{}

ACTION:
  help
    show this help
  import FILE
    import all the text content and metadata from FILE
    FILE: a json file obtained from archetype API,
          see inline comment (handle_import)
'''.format(self.help))
