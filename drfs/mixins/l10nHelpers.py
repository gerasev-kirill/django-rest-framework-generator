# -*- coding: utf-8 -*-
import json
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile



def get_options_from_request_data(fields):
    """
        На вход подается объект request.data
        --
        возвращает (dict, InMemoryUploadedFile)
    """
    allowedOptions = ['maxWidth', 'maxHeight', 'skipGif', 'saveToLocalStorage',
                      'quality', 'thumbSizes', 'forIdInList', 'addWatermark']
    options = {}
    _file = None

    for key in fields.keys():
        value = fields[key]
        if isinstance(value, InMemoryUploadedFile) or isinstance(value, TemporaryUploadedFile):
            _file = value
            continue
        if key.startswith('options_'):
            key = key.replace('options_', '')
            if key not in allowedOptions:
                continue
            if isinstance(value, list):
                if not value:
                    continue
                value = value[0]
            if key.find('max') > -1 or key.find('quality') > -1:
                try:
                    value = int(value)
                    options[key] = value
                except:
                    continue
            if key in ['skipGif', 'saveToLocalStorage', 'addWatermark']:
                if value == 'true':
                    options[key] = True
                else:
                    options[key] = False
            if key == 'thumbSizes':
                try:
                    options['thumbSizes'] = json.loads(value)
                except:
                    pass
            if key == 'forIdInList':
                try:
                    options[key] = int(value)
                except:
                    pass
    return options, _file
