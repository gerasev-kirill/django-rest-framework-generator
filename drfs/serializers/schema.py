
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _


class EmptyJsonSerializer(serializers.Serializer):
    pass

class CountQuerysetSerializer(serializers.Serializer):
    count = serializers.IntegerField(label=_("Items count"))


class ExistsQuerysetSerializer(serializers.Serializer):
    exists = serializers.BooleanField(label=_("Is filtered queryset exists"))
