# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from rest_framework import exceptions
from django.core.files.uploadedfile import InMemoryUploadedFile






class L10nFileListMixin(object):

    def check_upload_field_exists(self, forModelField):
        queryset = self.get_queryset()
        modelClass = queryset.model
        exist = False

        for field in modelClass._meta.get_fields():
            if field.name == forModelField:
                exist = True
                break
        if not exist:
            raise exceptions.NotAcceptable(detail="Unknown field \""+forModelField+"\" for model \""+modelClass._meta.object_name+"\".")
        return True

    def get_l10nfile_id_from_options(self, data):
        forIdInList = data.get('options_forIdInList', -1)
        try:
            forIdInList = int(forIdInList)
        except:
            pass
        return forIdInList

    def get_l10nfile_data(self, objects=None, pks=None):
        from ..models import L10nFile
        from ..serializers.models import L10nFile as L10nFileSerializer
        if pks:
            objects = L10nFile.objects.filter(pk__in=pks)
        ser = L10nFileSerializer(objects, many=True)
        return ser.data

    @detail_route(url_path="fileList/(?P<forModelField>[^/.]+)/upload", methods=['post'])
    def upload_file_to_list(self, request, *args, **kwargs):
        from ..models import L10nFile
        forModelField = kwargs.get('forModelField', None)
        forIdInList = self.get_l10nfile_id_from_options(request.data)
        self.check_upload_field_exists(forModelField)
        instance = self.get_object()
        fileList = getattr(instance, forModelField)
        ffile = None

        for k in request.data.keys():
            if isinstance(request.data[k], InMemoryUploadedFile):
                ffile = request.data[k]
                break

        if not ffile:
            raise exceptions.NotAcceptable(detail="Can't find field with file in formdata.")

        meta = {
            'size': ffile._size,
            'originalName': ffile._name,
            'type': ffile.content_type
        }
        if forIdInList < 0 or forIdInList not in fileList:
            l10nFile = L10nFile.objects.create(file_data=ffile, meta_data=meta)
            fileList.append(l10nFile.id)
            setattr(instance, forModelField, fileList)
            instance.save()
        elif forIdInList in fileList:
            l10nFile = L10nFile.objects.get(pk=forIdInList)
            l10nFile.delete_file_data()
            l10nFile.file_data = ffile
            l10nFile.meta_data = meta
            l10nFile.save()

        return Response(self.get_l10nfile_data(pks=fileList))



    @detail_route(url_path="fileList/(?P<forModelField>[^/.]+)/update", methods=['put'])
    def update_files_inside_list(self, request, *args, **kwargs):
        from ..models import L10nFile
        forModelField = kwargs.get('forModelField', None)
        self.check_upload_field_exists(forModelField)
        instance = self.get_object()
        fileList = getattr(instance, forModelField)

        def update_l10nfile(l10nFile):
            data = {}
            title = None
            description = None
            for obj in request.data:
                if obj.get('id', -1) == l10nFile.id:
                    title = obj.get('en', {}).get('title', None)
                    description = obj.get('en', {}).get('description', None)
                    if title:
                        l10nFile.title = title
                    if description:
                        l10nFile.description = description
                    break
            if title or description:
                l10nFile.save()

        objects = L10nFile.objects.filter(pk__in=fileList)
        for l10nFile in objects:
            update_l10nfile(l10nFile)

        return Response(self.get_l10nfile_data(objects=objects))


    @detail_route(url_path="fileList/(?P<forModelField>[^/.]+)/delete", methods=['patch'])
    def delete_files_inside_list(self, request, *args, **kwargs):
        from ..models import L10nFile
        forModelField = kwargs.get('forModelField', None)
        self.check_upload_field_exists(forModelField)
        instance = self.get_object()
        fileList = getattr(instance, forModelField)

        to_delete = []
        for obj in request.data:
            if obj.get('id', -1) in fileList:
                to_delete.append(obj['id'])
                fileList.remove(obj['id'])

        L10nFile.objects.filter(pk__in=to_delete).delete()
        setattr(instance, forModelField, fileList)
        instance.save()

        return Response(self.get_l10nfile_data(pks=fileList))