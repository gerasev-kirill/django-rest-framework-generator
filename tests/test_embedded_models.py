from django.test import TestCase
import drfs, json




class Serializer(TestCase):

    def test_selializergen(self):
        modelClass = drfs.generate_model('TestModelWithEmbeddedOne.json')
        one_embedded =  modelClass._meta.get_fields()[-1]
        serializerClass = drfs.generate_serializer(modelClass)

        obj = modelClass.objects.create(one_embedded={'estring': 'world'})

        ser = serializerClass(data={'one_embedded': {'estring': 'world'}})
        self.assertTrue(ser.is_valid())

        instance = ser.save()
        self.assertEqual(
            instance.one_embedded['estring'],
            'world'
        )
        self.assertEqual(
            instance.one_embedded['eint'],
            90
        )

        ser = serializerClass(data={'one_embedded': {'estring': 'world2', 'eint': 20}})
        self.assertTrue(ser.is_valid())

        instance = ser.save()
        self.assertEqual(
            instance.one_embedded['estring'],
            'world2'
        )
        self.assertEqual(
            instance.one_embedded['eint'],
            20
        )

        ser = serializerClass(data={'many_embedded': [
            {'estring': 'world2'},
            {'eint': 5},
            {'estring': 'withembedded2', 'one_embedded2': {'eint2': 8}}
        ]})
        self.assertTrue(ser.is_valid())

        instance = ser.save()
        self.assertListEqual(
            instance.many_embedded,
            [
                {'estring': 'world2', 'eint': 90},
                {'eint': 5},
                {'estring': 'withembedded2', 'one_embedded2': {'eint2': 8}, u'eint': 90}
            ]
        )
