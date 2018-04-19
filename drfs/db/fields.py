import json
from jsonfield import JSONField

from .validators import EmbeddedValidator



class ListField(JSONField):
    pass


class GeoPoint(JSONField):
    pass



class EmbeddedOneModel(JSONField):
    def __init__(self, *args, **kwargs):
        if 'embedded_model_name' in kwargs:
            self.embedded_model_name = kwargs['embedded_model_name']
            del kwargs['embedded_model_name']
            self.embedded_validator = EmbeddedValidator(self.embedded_model_name)
            kwargs['validators'] = kwargs.get('validators', None) or []
            kwargs['validators'].append(EmbeddedValidator(self.embedded_model_name))
        super(EmbeddedOneModel, self).__init__(*args, **kwargs)

    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert JSON object to a string"""
        if self.null and value is None:
            return None
        value = self.embedded_validator.validate_data(value)
        return json.dumps(value, **self.dump_kwargs)




class EmbeddedManyModel(JSONField):
    def __init__(self, *args, **kwargs):
        if 'embedded_model_name' in kwargs:
            self.embedded_model_name = kwargs['embedded_model_name']
            del kwargs['embedded_model_name']
            self.embedded_validator = EmbeddedValidator(self.embedded_model_name)
            kwargs['validators'] = kwargs.get('validators', None) or []
            kwargs['validators'].append(EmbeddedValidator(self.embedded_model_name))
        super(EmbeddedManyModel, self).__init__(*args, **kwargs)

    def _validate_value(self, value):
        if not self.embedded_validator:
            return value
        i = 0
        for item in value or []:
            value[i] = self.embedded_validator.validate_data(item)
            i += 1
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert JSON object to a string"""
        if self.null and value is None:
            return None
        value = self._validate_value(value)
        return json.dumps(value, **self.dump_kwargs)
