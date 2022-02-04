from rest_framework import serializers, fields
import json, six

FLOAT_TYPES = tuple([float] + list(six.integer_types))




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





class GeoPoint(JSONField):
    custom_error_messages = {
        'no_lat_lng': "Please provide 'lat' and 'lng' value. Ex.: {'lat': 0.3, 'lng': 32.122}",
        'invalid_lat_lng_type': "Invalid type for property '{field}'. Expected <type 'int'> or <type 'float'>, got {type}",
        'invalid_text_type': "Invalid type for property 'text'. Expected <type 'str'>, got {type}"
    }

    def __init__(self, *args, **kwargs):
        super(GeoPoint, self).__init__(*args, **kwargs)

        def geo_point_validator(value):
            if not value and not self.required:
                return
            if not isinstance(value, dict):
                raise serializers.ValidationError(self.default_error_messages['invalid'])
            if 'lat' not in value or 'lng' not in value:
                raise serializers.ValidationError(self.custom_error_messages['no_lat_lng'])
            if not isinstance(value['lat'], FLOAT_TYPES) or isinstance(value['lat'], bool):
                raise serializers.ValidationError(self.custom_error_messages['invalid_lat_lng_type'].format(
                    field='lat',
                    type=type(value['lat'])
                ))
            if not isinstance(value['lng'], FLOAT_TYPES) or isinstance(value['lng'], bool):
                raise serializers.ValidationError(self.custom_error_messages['invalid_lat_lng_type'].format(
                    field='lng',
                    type=type(value['lng'])
                ))
            if 'text' in value and not isinstance(value['text'], six.text_type):
                raise serializers.ValidationError(self.custom_error_messages['invalid_text_type'].format(
                    type=type(value['text'])
                ))

            # clean up value
            keys_to_remove = [
                k
                for k in value if k not in ['lat', 'lng', 'text']
            ]
            for k in keys_to_remove:
                del value[k]

        self.validators.append(geo_point_validator)



class EmbeddedOneModel(JSONField):
    embedded_validator = None

    def __init__(self, *args, **kwargs):
        from drfs.db.validators import EmbeddedValidator
        if 'embedded_model_name' in kwargs:
            self.embedded_validator = EmbeddedValidator(
                kwargs['embedded_model_name'],
                params=kwargs.get('embedded_params', None)
            )
            del kwargs['embedded_model_name']
            del kwargs['embedded_params']

        super(EmbeddedOneModel, self).__init__(*args, **kwargs)

        def validator(data):
            if not self.embedded_validator:
                return True
            validated = self.embedded_validator.validate_data(data)
            if data:
                for k,v in validated.items():
                    data[k] = v
                for k,v in data.items():
                    if k not in data:
                        del data[k]
            return True

        self.validators.append(validator)


class EmbeddedManyModel(ListField):
    embedded_validator = None

    def __init__(self, *args, **kwargs):
        from drfs.db.validators import EmbeddedValidator
        if 'embedded_model_name' in kwargs:
            self.embedded_validator = EmbeddedValidator(
                kwargs['embedded_model_name'],
                params=kwargs.get('embedded_params', None)
            )
            del kwargs['embedded_model_name']
            del kwargs['embedded_params']

        super(EmbeddedManyModel, self).__init__(*args, **kwargs)

        def validator(data):
            if not self.embedded_validator:
                return True
            i = 0
            for item in data or []:
                data[i] = self.embedded_validator.validate_data(item)
                i += 1
            return True

        self.validators.append(validator)


class EmbeddedManyAsObjectModel(JSONField):
    embedded_validator = None

    def __init__(self, *args, **kwargs):
        from drfs.db.validators import EmbeddedValidator
        if 'embedded_model_name' in kwargs:
            self.embedded_validator = EmbeddedValidator(
                kwargs['embedded_model_name'],
                params=kwargs.get('embedded_params', None)
            )
            del kwargs['embedded_model_name']
            del kwargs['embedded_params']

        super(EmbeddedManyAsObjectModel, self).__init__(*args, **kwargs)

        def validator(data):
            if not self.embedded_validator or not data:
                return True
            for key in data:
                data[key] = self.embedded_validator.validate_data(data[key])
            return True

        self.validators.append(validator)
