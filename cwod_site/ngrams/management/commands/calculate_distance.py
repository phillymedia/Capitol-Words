from itertools import combinations
from math import sqrt
from optparse import make_option
from scipy.spatial.distance import cosine as cosine_distance

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from ngrams.models import *

class Calculator(object):
    def __init__(self, field, models, keypair):
        self.models = models
        self.keypair = keypair
        self.ngram_map = {}
        for model in models:
            key = model.__dict__[field if not field == 'bioguide' else 'bioguide_id']
            try:
                self.ngram_map[model.ngram][key] = model.tfidf
            except KeyError:
                self.ngram_map[model.ngram] = {key: model.tfidf}

    def calculate(self):
        a = self.get_vector(self.keypair[0])
        b = self.get_vector(self.keypair[1])
        return cosine_distance(a, b)


    # def cosine_distance(self, a, b):
    #     '''Calculates the distance between n-dimensional vectors a, b
    #        http://stackoverflow.com/questions/1823293/optimized-method-for-calculating-cosine-distance-in-python
    #        '''
    #     if len(a) != len(b):
    #         raise ValueError, "a and b must be the same length"
    #     numerator = 0
    #     denoma = 0
    #     denomb = 0
    #     for i in range(len(a)):
    #         ai = a[i]
    #         bi = b[i]
    #         numerator += ai*bi
    #         denoma += ai*ai
    #         denomb += bi*bi
    #     result = 1 - numerator / (sqrt(denoma)*sqrt(denomb))
    #     return result

    def get_vector(self, key):
        return tuple([ngram.get(key, 0) for ngram in self.ngram_map.values()])


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--field',
                action='store',
                dest='field',
                default=None,
                help='Field to calculate ngram tfidf for'),
            make_option('--values',
                action='store',
                dest='values',
                default='',
                help='Specific values to limit calculations among'),
    )

    MODEL_MAP = {
        'date': NgramsByDate,
        'month': NgramsByMonth,
        'state': NgramsByState,
        'bioguide': NgramsByBioguide
        }

    def handle(self, *args, **options):
        field = options.get('field')
        if not field:
            raise Exception('You must specify a field! Options are: date, month, state, bioguide')
        values_to_compare = [value.strip() for value in options.get('values').split(',')]
        cursor = connections['ngrams'].cursor()
        query = 'SELECT DISTINCT %s from ngrams_ngramsby%s' % (field if not field == 'bioguide' else 'bioguide_id',
                                                               field)
        if len(values_to_compare):
            keys = set(values_to_compare)
        else:
            cursor.execute(query)
            keys = set([str(key[0]) for key in cursor.fetchall() if key[0]])
        pairs = combinations(keys, 2)

        for keypair in pairs:
            # with transaction.commit_on_success():
            current_models = self._get_models(self.field, keypair)
            calculator = Calculator(field, current_models, keypair)
            distance = calculator.calculate()
            # INSERT STUFF!
            print "%s to %s: %s" % (keypair[0], keypair[1], distance)

    def _get_models(self, field, values_to_compare):
        if values_to_compare:
            params = {'%s__in' % field: values_to_compare}
            ngrams = MODEL_MAP[field].objects.filter(**params)
        else:
            ngrams = MODEL_MAP[field].objects.all()

        return ngrams

