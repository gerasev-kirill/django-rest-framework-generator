from django.test import TestCase
from django.contrib.auth.models import User as UserModel
from django.db.models.fields.related import ForeignKey
import drfs, json


class Serializer(TestCase):

    def test_selializergen(self):
        modelClass = drfs.generate_model('TestModelForJsonData.json')
        serializerClass = drfs.generate_serializer(modelClass)
        ser = serializerClass(data={'required': {}})
        self.assertEqual(ser.is_valid(), True)

        ser = serializerClass(data={'required': {}, 'not_required': None})
        self.assertEqual(ser.is_valid(), True)

        ser = serializerClass(data={'required': {}, 'not_required': 'nnoooo'})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors['not_required'],
            ["Invalid JSON"]
        )

        ser = serializerClass(data={})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors,
            { 'required': ['This field is required.']}
        )

        ser = serializerClass(data={'required': None})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors,
            { 'required': ['This field may not be null.']}
        )


        ser = serializerClass(data={'required': {'some': 'value'}})
        ser.is_valid()
        instance = ser.create(ser.validated_data)
        self.assertEqual(
            instance.not_required,
            {'default': 'not_required'}
        )
