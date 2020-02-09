from django_model_changes import ChangesMixin
import os

from ... import helpers





class MetaAbstract:
    abstract = True

class MetaNoAbstract:
    abstract = False


class BaseModelGenerator(object):
    model_fields_mapping = {}
    default_model_class = None


    def __init__(self, model_definition, module_name, model_path=None, **kwargs):
        model_name = model_definition.get('name', None)
        if not model_name:
            raise "DRFS - generators: Please provide model name field 'name' in  model definition"
        self.model_definition = model_definition
        self.model_name = str(model_name)
        self.module_name = str(module_name)
        self.mixin_path = None
        if model_path:
            mixin_path = os.path.dirname(os.path.dirname(model_path))
            if os.path.isfile(os.path.join(mixin_path, 'model_mixins', self.model_name + '.py')):
                from django.conf import settings
                mixin_path = mixin_path.replace(settings.BASE_DIR, '')
                mixin_path = '.'.join(mixin_path.split('/'))
                if not mixin_path:
                    mixin_path = os.path.basename(settings.BASE_DIR)
                if mixin_path[0] == '.':
                    mixin_path = mixin_path[1:]
                self.mixin_path = "{mixin_path}.model_mixins.{model_name}.ModelMixin".format(
                    model_name=self.model_name,
                    mixin_path=mixin_path
                )


    def get_model_class(self, model_path):
        if '.' not in model_path:
            return model_path
        return helpers.import_class(model_path)


    def build_field(self, name, params):
        if params['type'] in self.model_fields_mapping:
            field_class = self.model_fields_mapping[params['type']]
        else:
            try:
                field_class = helpers.import_class(params['type'])
            except ImportError:
                raise ValueError("DRFS - generators: No such field type '"+params['type']+"'. Field declared in '"+self.model_name+"' model")

        return field_class, [], {}


    def to_django_model(self):
        fields = {
            '__module__': self.module_name
        }
        fields_definition = list(self.model_definition.get('properties', {}).items()) + \
            list(self.model_definition.get('relations', {}).items())

        for field_name, field_params in fields_definition:
            if type(field_params) != type({}):
                raise Exception("DRFS - generators: Expect 'field_params' to be dict. Got '" + str(type(field_params)) + "'")
            if not field_params.get('type', None):
                raise Exception("DRFS - generators: No 'field' property in field_params definition for field generation")

            convert_func = getattr(self, 'build_field__'+ field_params['type'], None)
            convert_func = convert_func or self.build_field
            field_class, field_args, field_kwargs = convert_func(field_name, field_params)

            fields[field_name] = field_class(
                *field_args,
                **field_kwargs
            )


        base_class = helpers.import_class(
            self.model_definition.get('base', self.default_model_class)
        )
        mixin = None
        if self.mixin_path:
            try:
                mixin = helpers.import_class(self.mixin_path)
            except ImportError:
                mixin = None

        if self.model_definition.get('options', {}).get('abstract', False):
            fields['Meta'] = MetaAbstract
            if mixin:
                model_cls = type(self.model_name, (mixin, base_class), fields)
            else:
                model_cls = type(self.model_name, (base_class,), fields)
            model_cls._meta.abstract = True
            return model_cls

        fields['Meta'] = MetaNoAbstract

        classes = []
        if mixin:
            classes.append(mixin)
        if self.model_definition.get('options', {}).get('changes', True):
            classes.append(ChangesMixin)
        classes.append(base_class)

        model_cls = type(self.model_name, tuple(classes), fields)
        setattr(model_cls, 'DRFS_MODEL_DEFINITION', self.model_definition)
        return model_cls
