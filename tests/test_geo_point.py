from django.test import TestCase
from django.contrib.auth.models import User as UserModel
from django.db.models.fields.related import ForeignKey
import drfs, json

from drfs.serializers.fields import GeoPoint as GeoPointSerializer


class Serializer(TestCase):

    def test_selializergen(self):
        modelClass = drfs.generate_model('TestModelForGeoPoint.json')
        serializerClass = drfs.generate_serializer(modelClass)

        ser = serializerClass(data={'geo_point': ['invalid data']})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors, {
                'geo_point': ['Value must be valid JSON.']
            }
        )

        ser = serializerClass(data={'geo_point': {'key': 'invalid data'}})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors, {
                'geo_point': [
                    """Please provide 'lat' and 'lng' value. Ex.: {'lat': 0.3, 'lng': 32.122}"""
                ]
            }
        )

        ser = serializerClass(data={'geo_point': {'lat': 'invalid data', 'lng': 0}})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors, {
                'geo_point': [
                    GeoPointSerializer.custom_error_messages['invalid_lat_lng_type'].format(
                        field='lat',
                        type=type('')
                    )
                ]
            }
        )

        ser = serializerClass(data={'geo_point': {'lat': 0, 'lng': False}})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors, {
                'geo_point': [
                    GeoPointSerializer.custom_error_messages['invalid_lat_lng_type'].format(
                        field='lng',
                        type=type(False)
                    )
                ]
            }
        )

        ser = serializerClass(data={'geo_point': {'lat': 0, 'lng': 0, 'text': False}})
        self.assertEqual(ser.is_valid(), False)
        self.assertEqual(
            ser.errors, {
                'geo_point': [
                    GeoPointSerializer.custom_error_messages['invalid_text_type'].format(
                        type=type(False)
                    )
                ]
            }
        )

        data = {
            'geo_point': {
                'lat': 0,
                'lng': 0,
                'field_to_remove': 'clean_me!'
            }
        }
        ser = serializerClass(data=data)
        ser.is_valid()
        self.assertEqual(
            ser.validated_data, {
                'geo_point': {
                    'lat': 0,
                    'lng': 0
                }
            }
        )
