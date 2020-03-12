from django.test import TestCase
from django.core.management import call_command
from ctrs_texts.models import EncodedText
from . import utils

ARC_TEXT_JSON_PATH = 'arc-content.json'


class TextTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # from django.db import connection
        # print(connection.settings_dict)

        text = EncodedText.objects.first()
        if not text:
            call_command('ctrstxt', 'import', ARC_TEXT_JSON_PATH)

    def test_sentences(self):
        '''Sentence extraction'''
        # self.assertFalse(False, 'false')
        # self.assertEqual(cat.speak(), 'The cat says "meow"')

        empty_sentence_count = 0
        sentence_count = 0

        ets = EncodedText.objects.order_by(
            'abstracted_text__group__short_name',
            'abstracted_text__short_name'
        )

        for et in ets:
            siglum = et.abstracted_text.short_name
            if 0 and siglum not in ['O']:
                continue
            if not siglum:
                continue
            empty_sentences = []

            for sentence_number in range(1, 28):
                sentence_count += 1
                sentence = utils.get_sentence_from_text(et, sentence_number)
                if not sentence:
                    empty_sentences.append(sentence_number)
                    empty_sentence_count += 1

            if empty_sentences:
                print(siglum, et.type.slug)
                # print(repr(et.content[:1000]))
                print(', '.join([str(sn) for sn in empty_sentences]))

        print('{} empty sentences, {} total'.format(
            empty_sentence_count, sentence_count)
        )

        self.assertEqual(empty_sentence_count, 0)
