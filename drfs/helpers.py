# -*- coding: utf-8 -*-
import rest_framework
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
