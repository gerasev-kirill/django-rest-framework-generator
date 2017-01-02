# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from rest_framework import exceptions

from .l10nHelpers import get_options_from_request_data





class L10nFileMixin(object):
    l10nfile_allowed_fields = ('mainImg',)

    def check_upload_l10nfile_field_exists(self, forModelField):
        queryset = self.get_queryset()
        modelClass = queryset.model
        exist = False

        for field in modelClass._meta.get_fields():
            if field.name == forModelField:
                exist = True
                break
        if not exist or forModelField not in self.l10nfile_allowed_fields:
            raise exceptions.NotAcceptable(detail="Unknown L10nFile field \""+forModelField+"\" for model \""+modelClass._meta.object_name+"\".")
        return True

    def get_l10nfile_data(self, obj=None, pk=None):
        from ..models import L10nFile
        from ..serializers.models import L10nFile as L10nFileSerializer
        if pk:
            try:
                obj = L10nFile.objects.filter(pk=pk)
            except:
                pass
        ser = L10nFileSerializer(obj)
        return ser.data

    @detail_route(url_path="file/(?P<forModelField>[^/.]+)/upload", methods=['post'])
    def upload_file(self, request, *args, **kwargs):
        from ..models import L10nFile
        forModelField = kwargs.get('forModelField', None)
        self.check_upload_l10nfile_field_exists(forModelField)
        instance = self.get_object()
        oldFfile = getattr(instance, forModelField, None)
        options, ffile = get_options_from_request_data(request.data)

        if not ffile:
            raise exceptions.NotAcceptable(detail="Can't find field with file in formdata.")

        meta = {
            'size': ffile._size,
            'originalName': ffile._name,
            'type': ffile.content_type
        }
        l10nFile = L10nFile(file_data=ffile, meta_data=meta)
        l10nFile.save(options=options)
        setattr(instance, forModelField, l10nFile)
        instance.save()
        if oldFfile:
            oldFfile.delete_file_data()
            oldFfile.delete()

        return Response(self.get_l10nfile_data(obj=l10nFile))



    @detail_route(url_path="file/(?P<forModelField>[^/.]+)/update", methods=['put'])
    def update_file(self, request, *args, **kwargs):
        from ..models import L10nFile
        forModelField = kwargs.get('forModelField', None)
        self.check_upload_l10nfile_field_exists(forModelField)
        instance = self.get_object()
        oldFfile = getattr(instance, forModelField)
        if not oldFfile:
            return Response(None)

        def update_l10nfile(l10nFile):
            data = {}
            title = None
            description = None
            obj = request.data
            if obj.get('id', -1) == l10nFile.id:
                title = obj.get('en', {}).get('title', None)
                description = obj.get('en', {}).get('description', None)
                if title:
                    l10nFile.title = title
                if description:
                    l10nFile.description = description
            if title or description:
                l10nFile.save()

        update_l10nfile(oldFfile)
        return Response(self.get_l10nfile_data(obj=oldFfile))


    @detail_route(url_path="file/(?P<forModelField>[^/.]+)/delete", methods=['patch'])
    def delete_file(self, request, *args, **kwargs):
        from ..models import L10nFile
        forModelField = kwargs.get('forModelField', None)
        self.check_upload_l10nfile_field_exists(forModelField)
        instance = self.get_object()
        oldFfile = getattr(instance, forModelField)
        if oldFfile:
            oldFfile.delete_file_data()
            oldFfile.delete()
            setattr(instance, forModelField, None)
            instance.save()

        return Response(None, 204)
