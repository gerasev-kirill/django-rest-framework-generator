from django.test import TestCase


class Fail(TestCase):

    def test_string_representation(self):
        self.fail("TODO Test incomplete")
