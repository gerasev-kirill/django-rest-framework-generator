from . import mixins
from .serializergen import SerializerGenFactory
from .viewsetgen import ViewsetGenFactory
import json, os, errno
from django.conf import settings

from generators.model import DjangoOrmModelGenerator


def find_model_definition(name):
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
    return (module_name, path)


def get_model(name, app=None):
    from django.apps import apps
    model = None
    name = name.replace('.json','').lower()
    if app:
        model = apps.get_model(app, name)
    else:
        for m_name, m_models in apps.all_models.items():
            if m_models.has_key(name):
                model = m_models[name]
                break
    return model


def generate_model(name):
    name = os.path.basename(name)
    model = get_model(name)
    if model:
        return model

    module_name, path = find_model_definition(name)
    if not module_name and not path:
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            name
        )

    with open(path) as f:
        definition = json.load(f)

    name = definition.get('name', name)
    converter = DjangoOrmModelGenerator(definition, module_name)
    return converter.to_django_model()



def generate_serializer(model_class, **kwargs):
    if isinstance(model_class, str):
        model_class = generate_model(model_class)
    return SerializerGenFactory(model_class, **kwargs)


def generate_viewset(model_class, **kwargs):
    if isinstance(model_class, str):
        model_class = generate_model(model_class)
    return ViewsetGenFactory(model_class, **kwargs)
