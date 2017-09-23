from rest_framework import serializers, fields
from django.utils import six
import json







class JSONField(fields.JSONField):
    def to_representation(self, value):
        if self.binary:
            value = json.dumps(value)
            # On python 2.x the return type for json.dumps() is underspecified.
            # On python 3.x json.dumps() returns unicode strings.
            if isinstance(value, six.text_type):
                value = bytes(value.encode('utf-8'))
        if isinstance(value, dict):
            return value
        if isinstance(value, six.string_types) or isinstance(value, six.text_type):
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
        if isinstance(value, dict):
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
        if isinstance(value, dict):
            return value
        if isinstance(value, six.string_types) or isinstance(value, six.text_type):
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
        if isinstance(value, list):
            return value
        try:
            value = data.replace("u'", "\"")
            value = value.replace("'", "\"")
            json.loads(value)
        except:
            raise serializers.ValidationError('Invalid Array')
        return value
