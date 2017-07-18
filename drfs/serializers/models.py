from rest_framework import serializers
from django.conf import settings
from ..models import L10nFile as L10nFileModelClass



class L10nFile(serializers.HyperlinkedModelSerializer):
    default = serializers.SerializerMethodField()
    en = serializers.SerializerMethodField()

    def get_default(self, obj):
        return 'en'

    def get_en(self, obj):
        if isinstance(obj, int):
            try:
                obj = L10nFileModelClass.objects.get(id=obj)
            except:
                return None
        if not obj:
            return obj
        name = str(obj.file_data)
        name = name.replace(settings.MEDIA_ROOT, '')
        if name[0] == '/':
            name = name[1:]
        data = {
            'meta': obj.meta_data,
            'thumbs': obj.thumbs or [],
            'name': name,
            'title': obj.title,
            'description': obj.description
        }
        return data

    class Meta:
        model = L10nFileModelClass
        fields = ('id', 'default', 'en')
