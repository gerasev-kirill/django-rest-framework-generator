# -*- coding: utf-8 -*-
import rest_framework, os, json
from django.db.models import IntegerField, BigIntegerField, PositiveIntegerField, PositiveSmallIntegerField, SmallIntegerField

rest_framework_version = tuple([
    int(x)
    for x in rest_framework.VERSION.split('.')
])



try:
    from django.db.models import PositiveBigIntegerField

    def is_integer_field(django_field):
        return isinstance(django_field, (IntegerField, BigIntegerField, PositiveIntegerField, PositiveSmallIntegerField, SmallIntegerField, PositiveBigIntegerField))

except ImportError:
    def is_integer_field(django_field):
        return isinstance(django_field, (IntegerField, BigIntegerField, PositiveIntegerField, PositiveSmallIntegerField, SmallIntegerField))




def import_class(cl):
    cl = str(cl)
    if '.site-packages.' in cl:
        cl = cl.split('.site-packages.')[-1]
    # http://stackoverflow.com/questions/547829/how-to-dynamically-load-a-python-class
    d = cl.rfind(".")
    classname = cl[d+1:len(cl)]
    m = __import__(cl[0:d], {}, {}, [classname])
    return getattr(m, classname)




def load_embedded_model(name):
    from django.apps import apps
    model_schema = None
    if os.path.splitext(name)[-1] != '.json':
        name = name + '.json'

    for app in apps.get_app_configs():
        fpath = os.path.join(app.path, 'embedded_models.json', name)
        if not os.path.isfile(fpath):
            continue
        with open(fpath) as f:
            try:
                model_schema = json.load(f)
            except Exception as e:
                raise Exception("Unable to parse {file}. {error}".format(file=fpath, error=e))
        break
    return model_schema



def fix_field_choices(choices):
    if not isinstance(choices[0], tuple) and not isinstance(choices[0], list):
        if isinstance(choices[0], tuple) or isinstance(choices[0], list):
            return tuple([
                tuple(c)
                for c in choices
            ])
        return tuple([
            (c, c)
            for c in choices
        ])
    return tuple(choices)



def field_choice_description_to_varname(choice: str):
    from unidecode import unidecode

    choice = u'' + choice
    bad_chars = [
        ':', '"', "'", '\\', '|', '?', '*',
        '\t', '\n', '\r', '\0', '%', '@', '!', '&', '=', '#', '^', ',',
        '(', ')'
    ]
    for i in bad_chars:
        choice = choice.replace(i, '', 10)
    choice = choice.translate(',/\\+.') \
            .replace('+', 'plus') \
            .replace('>', 'more_than') \
            .replace('<', 'less_than') \
            .replace('-', ' ') \
            .replace('/', ' ') \
            .replace('  ', ' ') \
            .replace('  ', ' ') 
    choice = '_'.join(choice.split(' ')).upper() or 'EMPTY'
    if choice[0].isnumeric():
        choice = 'VAR_' + choice
    return unidecode(choice)

