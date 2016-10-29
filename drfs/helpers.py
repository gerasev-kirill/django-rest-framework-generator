# -*- coding: utf-8 -*-
import os, math
from django.conf import settings
from PIL import Image
from cStringIO import StringIO

DEFAULT_IMG_CONF = {
    "maxWidth": 2000,
    "maxHeight": 2000,
    "quality": 70,
    "skipGif": True,
    "thumbSizes": ["70x70", "350x350", "440x250"]
}




def import_class(cl):
    cl = str(cl)
    # http://stackoverflow.com/questions/547829/how-to-dynamically-load-a-python-class
    d = cl.rfind(".")
    classname = cl[d+1:len(cl)]
    m = __import__(cl[0:d], {}, {}, [classname])
    return getattr(m, classname)



def resize_and_crop_img(img, modified_path, size, quality=90):
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the
    # ratio
    if ratio > img_ratio:
        img = img.resize((size[0], size[0] * img.size[1] / img.size[0]),
                         Image.ANTIALIAS)
        box = (0, (img.size[1] - size[1]) / 2, img.size[
               0], (img.size[1] + size[1]) / 2)
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((size[1] * img.size[0] / img.size[1], size[1]),
                         Image.ANTIALIAS)
        box = ((img.size[0] - size[0]) / 2, 0, (
            img.size[0] + size[0]) / 2, img.size[1])
        img = img.crop(box)
    else:
        img = img.resize((size[0], size[1]),
                         Image.ANTIALIAS)
        # If the scale is the same, we do not need to crop
    return img.save(modified_path, quality=quality)


def process_l10nFile(l10nFile, options={}, thumbSizeList=DEFAULT_IMG_CONF['thumbSizes']):
    if 'image' not in l10nFile.meta_data['type']:
        return
    """
        Ресайзит изображение к размерам ограничивающего прямоугольника.
        Только для локальных файлов.
    """
    if not options.has_key('maxWidth'):
        options['maxWidth'] = DEFAULT_IMG_CONF['maxWidth']
    if not options.has_key('maxHeight'):
        options['maxHeight'] = DEFAULT_IMG_CONF['maxHeight']
    if not options.has_key('quality'):
        options['quality'] =  DEFAULT_IMG_CONF['quality']
    if not options.has_key('skipGif'):
        options['skipGif'] = DEFAULT_IMG_CONF['skipGif']


    img = Image.open(l10nFile.file_data)
    ext = os.path.splitext(l10nFile.meta_data['originalName'])[-1].lower()
    img_width, img_height = img.size
    size = {
        'width': img_width,
        'height': img_height
    }

    if not options['skipGif'] and ext!='.gif':
        # ресайзим картинку в ограничивающие размеры
        # если картинка - не gif
        if img_width > options['maxWidth']:
            size['width'] = options['maxWidth']
        if img_height > options['maxHeight']:
            size['height'] = options['maxHeight']

        image.thumbnail(
            (size['width'], size['height']),
            Image.ANTIALIAS
        )
        img.save(str(l10nFile.file_data), quality=options['quality'])

    l10nFile.meta_data['width'] = size['width']
    l10nFile.meta_data['height'] = size['height']


    """
        Генерация превью картинки.
        Функция вырезает по центру область в отмасшатабированной
        картинке до размеров thumbSize.

        thumbSize    in    [  70, {width:90, height:120}, "200x130"  ]
    """
    tslist = []
    for thumbSize in thumbSizeList:
        if isinstance(thumbSize, int):
            # размер квадрата --  70 (в px)
            thumbSize = {
                'width': thumbSize,
                'height': thumbSize
            }
        elif isinstance(thumbSize, str):
            # размер прямоугольника -- "200x100" (в px)
            thumbSize = {
                'width': int(thumbSize.split('x')[0]),
                'height': int(thumbSize.split('x')[1])
            }
        tslist.append(thumbSize)

    thumbSizeList = tslist
    thumbNames = []
    localFilePath = str(l10nFile.file_data)
    if not os.path.isabs(localFilePath):
        localFilePath = os.path.join(settings.MEDIA_ROOT, localFilePath)

    for thumbSize in thumbSizeList:
        thumb = img
        name = str(thumbSize['width'])+"x"+str(thumbSize['height'])
        filename = localFilePath+".thumb."+name+".jpg"
        thumbNames.append(name)
        resize_and_crop_img(thumb, filename, (thumbSize['width'], thumbSize['height']), quality=87)

    l10nFile.thumbs = thumbNames
