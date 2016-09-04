from . import modelgen
from .serializergen import SerializerGenFactory
from .viewsetgen import ViewsetGenFactory
import json, os, errno
from django.conf import settings


class Cache:
    pass

models = Cache()

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



def generate_model(name):
    name = os.path.basename(name)
    model = getattr(models, name, None)
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
    model_class = modelgen.ModelGenFactory(definition, module_name)
    setattr(models, name, model_class)
    return model_class



def generate_serializer(model_class, **kwargs):
    if isinstance(model_class, str):
        model = getattr(models, model_class, None)
        if model:
            model_class = model
        else:
            model_class = generate_model(model_class)
    return SerializerGenFactory(model_class, **kwargs)


def generate_viewset(model_class, **kwargs):
    if isinstance(model_class, str):
        model = getattr(models, model_class, None)
        if model:
            model_class = model
        else:
            model_class = generate_model(model_class)
    return ViewsetGenFactory(model_class, **kwargs)
