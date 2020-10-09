from django.test import TestCase
import drfs




class Serializer(TestCase):

    def test_embedmodels(self):
        modelClass = drfs.generate_model('TestModelWithEmbeddedOne.json')
        #one_embedded =  modelClass._meta.get_field('one_embedded')
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

        # embedsMany validations
        # fail
        ser = serializerClass(data={'many_embedded': [
            {'estring': 'world2'},
            {'eint': 5},
            {'estring': 'withembedded2', 'one_embedded2': {'eint2': 8}, 'many_embedded2': None}
        ]})
        self.assertFalse(ser.is_valid())
        self.assertDictEqual(
            ser.errors,
            {u'many_embedded': [u"Key 'many_embedded2' error:\nNone should be instance of 'list'"]}
        )
        # ok
        ser = serializerClass(data={'many_embedded': [
            {'estring': 'world2'},
            {'eint': 5},
            {'estring': 'withembedded2', 'one_embedded2': {'eint2': 8}, 'many_embedded2': []}
        ]})
        self.assertTrue(ser.is_valid())

        # one of field validation error
        ser = serializerClass(data={'many_embedded': [
            {'estring': 'world2'},
            {'eint': 5},
            {'estring': 'withembedded2', 'one_embedded2': {'eint2': 8}, 'many_embedded2': [
                {'estring2': 10}
            ]}
        ]})
        self.assertFalse(ser.is_valid())
        self.assertIn(
            "Key 'many_embedded2' error:",
            ser.errors['many_embedded'][0]
        )
        self.assertIn(
            'estring2',
            ser.errors['many_embedded'][0]
        )

        # ok
        ser = serializerClass(data={'many_embedded': [
            {'estring': 'world2'},
            {'eint': 5},
            {'estring': 'withembedded2', 'one_embedded2': {'eint2': 8}, 'many_embedded2': [
                {'estring2': 'works!', 'eint2': 4},
                {'estring2': 'works2!'}
            ]}
        ]})
        self.assertTrue(ser.is_valid())
        instance = ser.save()
        self.assertListEqual(
            instance.many_embedded,
            [
                {'estring': 'world2', 'eint': 90},
                {'eint': 5},
                {'estring': 'withembedded2', 'one_embedded2': {'eint2': 8}, u'eint': 90, 'many_embedded2':[
                    {'estring2': 'works!', 'eint2': 4},
                    {'estring2': 'works2!'}
                ]}
            ]
        )
