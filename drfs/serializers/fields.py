from rest_framework import serializers, fields
from django.utils import six
import types, json








class JSONField(fields.JSONField):
    def to_representation(self, value):
        if self.binary:
            value = json.dumps(value)
            # On python 2.x the return type for json.dumps() is underspecified.
            # On python 3.x json.dumps() returns unicode strings.
            if isinstance(value, six.text_type):
                value = bytes(value.encode('utf-8'))
        if type(value) == types.DictType:
            return value
        if type(value) in [types.UnicodeType, types.StringType]:
            try:
                value = value.replace("u'", "\"")
                value = value.replace("'", "\"")
                return json.loads(value)
            except:
                pass
        return value

    def run_validation(self, data=fields.empty):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included
        in the input.

        May raise `SkipField` if the field should not be included in the
        validated data.
        """
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data
        value = self.to_internal_value(data)
        self.run_validators(value)
        if type(value) == types.DictType:
            return value
        try:
            value = data.replace("u'", "\"")
            value = value.replace("'", "\"")
            json.loads(value)
        except:
            raise serializers.ValidationError('Invalid JSON')
        return value


class ListField(fields.JSONField):
    def to_representation(self, value):
        if self.binary:
            value = json.dumps(value)
            # On python 2.x the return type for json.dumps() is underspecified.
            # On python 3.x json.dumps() returns unicode strings.
            if isinstance(value, six.text_type):
                value = bytes(value.encode('utf-8'))
        if type(value) == types.DictType:
            return value
        if type(value) in [types.UnicodeType, types.StringType]:
            try:
                value = value.replace("u'", "\"")
                value = value.replace("'", "\"")
                return json.loads(value)
            except:
                pass
        return value

    def run_validation(self, data=fields.empty):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included
        in the input.

        May raise `SkipField` if the field should not be included in the
        validated data.
        """
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data
        value = self.to_internal_value(data)
        self.run_validators(value)
        if type(value) == types.ListType:
            return value
        try:
            value = data.replace("u'", "\"")
            value = value.replace("'", "\"")
            json.loads(value)
        except:
            raise serializers.ValidationError('Invalid Array')
        return value
