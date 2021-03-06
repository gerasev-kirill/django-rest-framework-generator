from collections import namedtuple

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase, override_settings, testcases

from rest_framework import permissions, serializers, viewsets
#from rest_framework.decorators import action
from rest_framework.response import Response
#from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.test import APIRequestFactory

try:
    from django.urls import include, path, resolve, reverse
except ImportError:
    from django.conf.urls import include, url as path
    from django.core.urlresolvers import resolve, reverse

try:
    from rest_framework.test import URLPatternsTestCase
except ImportError:
    # drf < 3.12
    from importlib import import_module
    class URLPatternsTestCase(testcases.SimpleTestCase):
        """
        Isolate URL patterns on a per-TestCase basis. For example,
        class ATestCase(URLPatternsTestCase):
            urlpatterns = [...]
            def test_something(self):
                ...
        class AnotherTestCase(URLPatternsTestCase):
            urlpatterns = [...]
            def test_something_else(self):
                ...
        """
        @classmethod
        def setUpClass(cls):
            # Get the module of the TestCase subclass
            cls._module = import_module(cls.__module__)
            cls._override = override_settings(ROOT_URLCONF=cls.__module__)

            if hasattr(cls._module, 'urlpatterns'):
                cls._module_urlpatterns = cls._module.urlpatterns

            cls._module.urlpatterns = cls.urlpatterns

            cls._override.enable()
            super().setUpClass()

        @classmethod
        def tearDownClass(cls):
            super().tearDownClass()
            cls._override.disable()

            if hasattr(cls, '_module_urlpatterns'):
                cls._module.urlpatterns = cls._module_urlpatterns
            else:
                del cls._module.urlpatterns

try:
    from rest_framework.utils import json
except ImportError:
    """
    Wrapper for the builtin json module that ensures compliance with the JSON spec.
    REST framework should always import this wrapper module in order to maintain
    spec-compliant encoding/decoding. Support for non-standard features should be
    handled by users at the renderer and parser layer.
    """
    import functools
    import json as base_json


    def strict_constant(o):
        raise ValueError('Out of range float values are not JSON compliant: ' + repr(o))

    class FakeJson:
        @functools.wraps(base_json.loads)
        def loads(self, *args, **kwargs):
            kwargs.setdefault('parse_constant', strict_constant)
            return base_json.loads(*args, **kwargs)

    json = FakeJson()



from drfs.decorators import action
from drfs.routers import SimpleRouter, DefaultRouter
from drfs.helpers import rest_framework_version


factory = APIRequestFactory()


class RouterTestModel(models.Model):
    uuid = models.CharField(max_length=20)
    text = models.CharField(max_length=200)


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='routertestmodel-detail', lookup_field='uuid')

    class Meta:
        model = RouterTestModel
        fields = ('url', 'uuid', 'text')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = RouterTestModel.objects.all()
    serializer_class = NoteSerializer
    lookup_field = 'uuid'


class KWargedNoteViewSet(viewsets.ModelViewSet):
    queryset = RouterTestModel.objects.all()
    serializer_class = NoteSerializer
    lookup_field = 'text__contains'
    lookup_url_kwarg = 'text'


class MockViewSet(viewsets.ModelViewSet):
    queryset = None
    serializer_class = None


class EmptyPrefixSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RouterTestModel
        fields = ('uuid', 'text')


class EmptyPrefixViewSet(viewsets.ModelViewSet):
    queryset = [RouterTestModel(id=1, uuid='111', text='First'), RouterTestModel(id=2, uuid='222', text='Second')]
    serializer_class = EmptyPrefixSerializer

    def get_object(self, *args, **kwargs):
        index = int(self.kwargs['pk']) - 1
        return self.queryset[index]


class RegexUrlPathViewSet(viewsets.ViewSet):
    @action(detail=False, url_path='list/(?P<kwarg>[0-9]{4})')
    def regex_url_path_list(self, request, *args, **kwargs):
        kwarg = self.kwargs.get('kwarg', '')
        return Response({'kwarg': kwarg})

    @action(detail=True, url_path='detail/(?P<kwarg>[0-9]{4})')
    def regex_url_path_detail(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk', '')
        kwarg = self.kwargs.get('kwarg', '')
        return Response({'pk': pk, 'kwarg': kwarg})


notes_router = SimpleRouter()
notes_router.register(r'notes', NoteViewSet)

kwarged_notes_router = SimpleRouter()
kwarged_notes_router.register(r'notes', KWargedNoteViewSet)

namespaced_router = DefaultRouter()
namespaced_router.register(r'example', MockViewSet, basename='example')

empty_prefix_router = SimpleRouter()
empty_prefix_router.register(r'', EmptyPrefixViewSet, basename='empty_prefix')

regex_url_path_router = SimpleRouter()
regex_url_path_router.register(r'', RegexUrlPathViewSet, basename='regex')


class BasicViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'method': 'list'})

    @action(methods=['post'], detail=True)
    def action1(self, request, *args, **kwargs):
        return Response({'method': 'action1'})

    @action(methods=['post', 'delete'], detail=True)
    def action2(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @action(methods=['post'], detail=True)
    def action3(self, request, pk, *args, **kwargs):
        return Response({'post': pk})

    @action3.mapping.delete
    def action3_delete(self, request, pk, *args, **kwargs):
        return Response({'delete': pk})


class TestSimpleRouter(URLPatternsTestCase, TestCase):
    router = SimpleRouter()
    router.register('basics', BasicViewSet, basename='basic')

    urlpatterns = [
        path('api/', include(router.urls)),
    ]

    def setUp(self):
        self.router = SimpleRouter()

    def test_action_routes(self):
        # Get action routes (first two are list/detail)
        routes = list(reversed(
            self.router.get_routes(BasicViewSet)[:3]
        ))

        assert routes[0].url == '^{prefix}/{lookup}/action1{trailing_slash}$'
        assert routes[0].mapping == {
            'post': 'action1',
        }

        assert routes[1].url == '^{prefix}/{lookup}/action2{trailing_slash}$'
        assert routes[1].mapping == {
            'post': 'action2',
            'delete': 'action2',
        }

        assert routes[2].url == '^{prefix}/{lookup}/action3{trailing_slash}$'
        assert routes[2].mapping == {
            'post': 'action3',
            'delete': 'action3_delete',
        }

    def test_multiple_action_handlers(self):
        # Standard action
        response = self.client.post(reverse('basic-action3', args=[1]))
        assert response.data == {'post': '1'}

        # Additional handler registered with MethodMapper
        response = self.client.delete(reverse('basic-action3', args=[1]))
        assert response.data == {'delete': '1'}

    def test_register_after_accessing_urls(self):
        self.router.register(r'notes', NoteViewSet)
        assert len(self.router.urls) == 2  # list and detail
        self.router.register(r'notes_bis', NoteViewSet)
        assert len(self.router.urls) == 4


class TestRootView(URLPatternsTestCase, TestCase):
    urlpatterns = [
        path('non-namespaced/', include(namespaced_router.urls)),
        path('namespaced/', include((namespaced_router.urls, 'namespaced'), namespace='namespaced')),
    ]

    def test_retrieve_namespaced_root(self):
        response = self.client.get('/namespaced/')
        assert response.data == {"example": "http://testserver/namespaced/example/"}

    def test_retrieve_non_namespaced_root(self):
        response = self.client.get('/non-namespaced/')
        assert response.data == {"example": "http://testserver/non-namespaced/example/"}


class TestCustomLookupFields(URLPatternsTestCase, TestCase):
    """
    Ensure that custom lookup fields are correctly routed.
    """
    urlpatterns = [
        path('example/', include(notes_router.urls)),
        path('example2/', include(kwarged_notes_router.urls)),
    ]

    def setUp(self):
        RouterTestModel.objects.create(uuid='123', text='foo bar')
        RouterTestModel.objects.create(uuid='a b', text='baz qux')

    def test_custom_lookup_field_route(self):
        detail_route = notes_router.urls[-1]
        if hasattr(detail_route, 'pattern'):
            assert '<uuid>' in detail_route.pattern.regex.pattern
        else:
            assert '<uuid>' in detail_route._regex

    def test_retrieve_lookup_field_list_view(self):
        response = self.client.get('/example/notes/')
        assert response.data == [
            {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"},
            {"url": "http://testserver/example/notes/a%20b/", "uuid": "a b", "text": "baz qux"},
        ]

    def test_retrieve_lookup_field_detail_view(self):
        response = self.client.get('/example/notes/123/')
        assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"}

    def test_retrieve_lookup_field_url_encoded_detail_view_(self):
        response = self.client.get('/example/notes/a%20b/')
        assert response.data == {"url": "http://testserver/example/notes/a%20b/", "uuid": "a b", "text": "baz qux"}

class TestLookupValueRegex(TestCase):
    """
    Ensure the router honors lookup_value_regex when applied
    to the viewset.
    """
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()
            lookup_field = 'uuid'
            lookup_value_regex = '[0-9a-f]{32}'

        self.router = SimpleRouter()
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_urls_limited_by_lookup_value_regex(self):
        expected = ['^notes/$', '^notes/(?P<uuid>[0-9a-f]{32})/$']
        for idx in range(len(expected)):
            if hasattr(self.urls[idx], 'pattern'):
                assert expected[idx] == self.urls[idx].pattern.regex.pattern
            else:
                assert expected[idx] == self.urls[idx]._regex


@override_settings(ROOT_URLCONF='tests.test_routers_and_action_decorator')
class TestLookupUrlKwargs(URLPatternsTestCase, TestCase):
    """
    Ensure the router honors lookup_url_kwarg.

    Setup a deep lookup_field, but map it to a simple URL kwarg.
    """
    urlpatterns = [
        path('example/', include(notes_router.urls)),
        path('example2/', include(kwarged_notes_router.urls)),
    ]

    def setUp(self):
        RouterTestModel.objects.create(uuid='123', text='foo bar')

    def test_custom_lookup_url_kwarg_route(self):
        detail_route = kwarged_notes_router.urls[-1]
        if hasattr(detail_route, 'pattern'):
            assert '^notes/(?P<text>' in detail_route.pattern.regex.pattern
        else:
            assert '^notes/(?P<text>' in detail_route._regex

    def test_retrieve_lookup_url_kwarg_detail_view(self):
        response = self.client.get('/example2/notes/fo/')
        assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"}

    def test_retrieve_lookup_url_encoded_kwarg_detail_view(self):
        response = self.client.get('/example2/notes/foo%20bar/')
        assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"}

class TestTrailingSlashIncluded(TestCase):
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()

        self.router = SimpleRouter()
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_urls_have_trailing_slash_by_default(self):
        expected = ['^notes/$', '^notes/(?P<pk>[^/.]+)/$']
        for idx in range(len(expected)):
            if hasattr(self.urls[idx], 'pattern'):
                assert expected[idx] == self.urls[idx].pattern.regex.pattern
            else:
                assert expected[idx] == self.urls[idx]._regex


class TestTrailingSlashRemoved(TestCase):
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()

        self.router = SimpleRouter(trailing_slash=False)
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_urls_can_have_trailing_slash_removed(self):
        expected = ['^notes$', '^notes/(?P<pk>[^/.]+)$']
        for idx in range(len(expected)):
            if hasattr(self.urls[idx], 'pattern'):
                assert expected[idx] == self.urls[idx].pattern.regex.pattern
            else:
                assert expected[idx] == self.urls[idx]._regex



class TestNameableRoot(TestCase):
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()

        self.router = DefaultRouter()
        self.router.root_view_name = 'nameable-root'
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_router_has_custom_name(self):
        expected = 'nameable-root'
        assert expected == self.urls[-1].name


class TestActionKeywordArgs(TestCase):
    """
    Ensure keyword arguments passed in the `@action` decorator
    are properly handled.  Refs #940.
    """

    def setUp(self):
        class TestViewSet(viewsets.ModelViewSet):
            permission_classes = []

            @action(methods=['post'], detail=True, permission_classes=[permissions.AllowAny])
            def custom(self, request, *args, **kwargs):
                return Response({
                    'permission_classes': self.permission_classes
                })

        self.router = SimpleRouter()
        self.router.register(r'test', TestViewSet, basename='test')
        self.view = self.router.urls.get_url_pattern_by_name('test-custom').callback

    def test_action_kwargs(self):
        request = factory.post('/test/0/custom/')
        response = self.view(request)
        assert response.data == {'permission_classes': [permissions.AllowAny]}


class TestActionAppliedToExistingRoute(TestCase):
    """
    Ensure `@action` decorator raises an except when applied
    to an existing route
    """

    def test_exception_raised_when_action_applied_to_existing_route(self):
        class TestViewSet(viewsets.ModelViewSet):

            @action(methods=['post'], detail=True)
            def retrieve(self, request, *args, **kwargs):
                return Response({
                    'hello': 'world'
                })

        self.router = SimpleRouter()
        self.router.register(r'test', TestViewSet, basename='test')

        with pytest.raises(ImproperlyConfigured):
            self.router.urls


class DynamicListAndDetailViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'method': 'list'})

    @action(methods=['post'], detail=False)
    def list_route_post(self, request, *args, **kwargs):
        return Response({'method': 'action1'})

    @action(methods=['post'], detail=True)
    def detail_route_post(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @action(detail=False)
    def list_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @action(detail=True)
    def detail_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link2'})

    @action(detail=False, url_path="list_custom-route")
    def list_custom_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @action(detail=True, url_path="detail_custom-route")
    def detail_custom_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link2'})


class SubDynamicListAndDetailViewSet(DynamicListAndDetailViewSet):
    pass


class TestDynamicListAndDetailRouter(TestCase):
    def setUp(self):
        self.router = SimpleRouter()

    def _test_list_and_detail_route_decorators(self, viewset):
        routes = self.router.get_routes(viewset)
        #decorator_routes = [r for r in routes if not (r.name.endswith('-list') or r.name.endswith('-detail'))]
        def get_route(name):
            name = '{basename}-' + '-'.join(name.split('_'))
            for r in routes:
                if r.name == name:
                    return r
            return None

        MethodNamesMap = namedtuple('MethodNamesMap', 'method_name url_path')
        # Make sure all these endpoints exist and none have been clobbered
        for i, endpoint in enumerate([MethodNamesMap('list_custom_route_get', 'list_custom-route'),
                                      MethodNamesMap('list_route_get', 'list_route_get'),
                                      MethodNamesMap('list_route_post', 'list_route_post'),
                                      MethodNamesMap('detail_custom_route_get', 'detail_custom-route'),
                                      MethodNamesMap('detail_route_get', 'detail_route_get'),
                                      MethodNamesMap('detail_route_post', 'detail_route_post')
                                      ]):
            #route = decorator_routes[i]
            route = get_route(endpoint.method_name)
            # check url listing
            method_name = endpoint.method_name
            url_path = endpoint.url_path

            if method_name.startswith('list_'):
                assert route.url == '^{{prefix}}/{0}{{trailing_slash}}$'.format(url_path)
            else:
                assert route.url == '^{{prefix}}/{{lookup}}/{0}{{trailing_slash}}$'.format(url_path)
            # check method to function mapping
            if method_name.endswith('_post'):
                method_map = 'post'
            else:
                method_map = 'get'
            assert route.mapping[method_map] == method_name

    def test_list_and_detail_route_decorators(self):
        self._test_list_and_detail_route_decorators(DynamicListAndDetailViewSet)

    def _test_inherited_list_and_detail_route_decorators(self):
        self._test_list_and_detail_route_decorators(SubDynamicListAndDetailViewSet)


class TestEmptyPrefix(URLPatternsTestCase, TestCase):
    urlpatterns = [
        path('empty-prefix/', include(empty_prefix_router.urls)),
    ]

    def test_empty_prefix_list(self):
        response = self.client.get('/empty-prefix/')
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == [{'uuid': '111', 'text': 'First'},
                                                         {'uuid': '222', 'text': 'Second'}]

    def test_empty_prefix_detail(self):
        response = self.client.get('/empty-prefix/1/')
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'uuid': '111', 'text': 'First'}


class TestRegexUrlPath(URLPatternsTestCase, TestCase):
    urlpatterns = [
        path('regex/', include(regex_url_path_router.urls)),
    ]

    def test_regex_url_path_list(self):
        kwarg = '1234'
        response = self.client.get('/regex/list/{}/'.format(kwarg))
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'kwarg': kwarg}

    def test_regex_url_path_detail(self):
        pk = '1'
        kwarg = '1234'
        response = self.client.get('/regex/{}/detail/{}/'.format(pk, kwarg))
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'pk': pk, 'kwarg': kwarg}


if rest_framework_version >= (3,8,0):
    class TestViewInitkwargs(URLPatternsTestCase, TestCase):
        urlpatterns = [
            path('example/', include(notes_router.urls)),
        ]

        def test_suffix(self):
            match = resolve('/example/notes/')
            initkwargs = match.func.initkwargs

            assert initkwargs['suffix'] == 'List'

        def test_detail(self):
            match = resolve('/example/notes/')
            initkwargs = match.func.initkwargs
            assert not initkwargs['detail']

        def test_basename(self):
            match = resolve('/example/notes/')
            initkwargs = match.func.initkwargs

            assert initkwargs['basename'] == 'routertestmodel'
