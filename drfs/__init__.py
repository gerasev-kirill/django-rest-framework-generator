from . import helpers
from .viewsetgen import ViewsetGenFactory
import json, os, errno
from django.conf import settings



def find_model_definition(name, path=None):
    if os.path.isfile(path):
        module_name = None
        d = os.path.dirname(path)
        basename = os.path.basename(d)
        while basename:
            if basename not in ['__init__', 'models.json']:
                module_name = basename
                break
            d = os.path.dirname(d)
            basename = os.path.basename(d)
        return (module_name, path)

    path = None
    module_name = None
    for d in os.listdir(settings.BASE_DIR):
        if d[0] == '.':
            continue
        p = os.path.join(settings.BASE_DIR, d, 'models.json')
        if os.path.isdir(p):
            ld = os.listdir(p)
            if name in ld:
                path = os.path.join(p, name)
                module_name = d
                break
        if path:
            break
    if not path and not module_name:
        p = os.path.join(settings.BASE_DIR, 'models.json', name)
        if os.path.exists(p) and os.path.isfile(p):
            return (os.path.basename(settings.BASE_DIR), p)
    return (module_name, path)


__model_cache = {}
def get_model(name, app=None, latest=False):
    if latest:
        _name = name.replace('.json', '')
        if _name in __model_cache:
            return __model_cache[_name]

    from django.apps import apps
    model = None
    name = name.replace('.json','').lower()
    if app:
        model = apps.get_model(app, name)
    else:
        for m_name, m_models in apps.all_models.items():
            if name in m_models:
                model = m_models[name]
                break
    return model




def generate_model(path):
    name = os.path.basename(path)
    model = get_model(name)
    if model:
        return model

    module_name, path = find_model_definition(name, path)
    if not module_name and not path:
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            name
        )

    with open(path) as f:
        definition = json.load(f)

    if getattr(settings, 'DRF_GENERATOR', {}).get('model', {}).get('default_generator', None):
        MODEL_GENERATOR_CLASS = helpers.import_class(settings.DRF_GENERATOR['model']['default_generator'])
    else:
        from .generators.model import DjangoOrmModelGenerator
        MODEL_GENERATOR_CLASS = DjangoOrmModelGenerator
    converter = MODEL_GENERATOR_CLASS(definition, module_name, model_path=path)
    model = converter.to_django_model()
    __model_cache[model.__name__] = model
    return model



def generate_serializer(model_class, **kwargs):
    if isinstance(model_class, str):
        model_class = generate_model(model_class)

    if getattr(settings, 'DRF_GENERATOR', {}).get('serializer', {}).get('default_generator', None):
        SERIALIZER_GENERATOR_CLASS = helpers.import_class(settings.DRF_GENERATOR['serializer']['default_generator'])
    else:
        from .generators.serializer import DjangoRestSerializerGenerator
        SERIALIZER_GENERATOR_CLASS = DjangoRestSerializerGenerator
    generator = SERIALIZER_GENERATOR_CLASS(model_class, **kwargs)
    return generator.to_serializer()




def generate_viewset(model_class, **kwargs):
    if isinstance(model_class, str):
        model_class = generate_model(model_class)
    return ViewsetGenFactory(model_class, **kwargs)
