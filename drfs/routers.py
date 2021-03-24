
from collections import namedtuple
from django.core.exceptions import ImproperlyConfigured
from rest_framework.routers import SimpleRouter as BaseSimpleRouter, DefaultRouter as BaseDefaultRouter, Route
from rest_framework.routers import flatten
from . import helpers


try:
    from django.urls import re_path
except:
    # DEPRECATED: django < 2.0
    from django.conf.urls import url as re_path

try:
    from rest_framework.routers import escape_curly_brackets, DynamicRoute

    def replace_methodname(text, text2):
        return text

    def is_dynamic_list_route(route):
        return isinstance(route, DynamicRoute) and not route.detail

    def is_dynamic_detail_route(route):
        return isinstance(route, DynamicRoute) and route.detail


except ImportError:
    # DEPRECATED: drf < 3.8
    from rest_framework.routers import replace_methodname, DynamicDetailRoute as DynamicDeprecatedDetailRoute, DynamicListRoute as DynamicDeprecatedListRoute

    def escape_curly_brackets(url_path):
        """
        Double brackets in regex of url_path for escape string formatting
        """
        if ('{' and '}') in url_path:
            url_path = url_path.replace('{', '{{').replace('}', '}}')
        return url_path

    def is_dynamic_list_route(route):
        return isinstance(route, DynamicDeprecatedListRoute)

    def is_dynamic_detail_route(route):
        return isinstance(route, DynamicDeprecatedDetailRoute)


class ExtraAction:
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])



#
#
#


RouteDrfs = namedtuple('Route', ['url', 'mapping', 'name', 'detail', 'initkwargs', 'trailing_slash'])


class UrlPatternList(list):
    def get_url_pattern_by_name(self, name):
        for item in self:
            if item.name == name:
                return item
        return None



class SimpleRouter(BaseSimpleRouter):
    def _get_viewset_extra_actions(self, viewset):
        extra_actions = []
        for methodname in dir(viewset):
            if methodname.startswith("__"):
                continue
            attr = getattr(viewset, methodname)
            mapping = getattr(attr, 'mapping', None)
            if mapping:
                extra_actions.append(ExtraAction(
                    url=getattr(attr, 'url', None),
                    detail=getattr(attr, 'detail', True),
                    url_path=getattr(attr, 'url_path', None),
                    url_name=getattr(attr, 'url_name', None),
                    name=getattr(attr, 'name', None),
                    mapping=mapping,
                    kwargs=getattr(attr, 'kwargs', {}),
                    __name__=methodname,
                ))
        return extra_actions


    def register(self, prefix, viewset, base_name=None, basename=None):
        # старое название base_name (drf<3.11), новое - basename
        basename = base_name or basename
        if basename is None:
            if hasattr(self, 'get_default_basename'):
                # drf >= 3.11
                basename = self.get_default_basename(viewset)
            else:
                # DEPRECATED
                basename = self.get_default_base_name(viewset)
        self.registry.append((prefix, viewset, basename))
        # invalidate the urls cache
        if hasattr(self, '_urls'):
            del self._urls


    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.
        Returns a list of the Route namedtuple.
        """
        # converting to list as iterables are good for one pass, known host needs to be checked again and again for
        # different functions.
        known_actions = list(flatten([route.mapping.values() for route in self.routes if isinstance(route, Route)]))
        extra_actions = self._get_viewset_extra_actions(viewset)

        # checking action names against the known actions list
        not_allowed = [
            action.__name__ for action in extra_actions
            if action.__name__ in known_actions
        ]
        if not_allowed:
            msg = ('Cannot use the @action decorator on the following '
                   'methods, as they are existing routes: %s')
            raise ImproperlyConfigured(msg % ', '.join(not_allowed))

        # partition detail and list actions
        detail_actions = [action for action in extra_actions if action.detail]
        list_actions = [action for action in extra_actions if not action.detail]

        routes = []
        dynamic_routes = {}
        for route in self.routes:
            if is_dynamic_detail_route(route):
                for action in detail_actions:
                    r = self._get_dynamic_route(route, action, known_routes=dynamic_routes)
                    dynamic_routes[r.url] = r
            elif is_dynamic_list_route(route):
                for action in list_actions:
                    r = self._get_dynamic_route(route, action, known_routes=dynamic_routes)
                    dynamic_routes[r.url] = r
            else:
                routes.append(route)

        for full_url in dynamic_routes:
            routes.insert(0, dynamic_routes[full_url])
        return routes



    def _get_dynamic_route(self, route, action, known_routes={}):
        initkwargs = route.initkwargs.copy()
        initkwargs.update(action.kwargs)
        url_path = escape_curly_brackets(action.url_path)
        if helpers.rest_framework_version >= (3,9,0):
            route_kwargs = {
                'url': route.url.replace('{url_path}', url_path),
                'mapping': action.mapping,
                'name': route.name.replace('{url_name}', action.url_name),
                'trailing_slash': initkwargs.pop("trailing_slash", None),
                'detail': route.detail,
                'initkwargs': initkwargs
            }
        else:
            # DEPRECATED: drf < 3.9
            route_kwargs = {
                'url': replace_methodname(route.url, url_path),
                'mapping': action.mapping,
                'name': replace_methodname(route.name, action.url_name),
                'trailing_slash': initkwargs.pop("trailing_slash", None),
                'detail': action.detail,
                'initkwargs': initkwargs,
            }
        # сверяемся, чтоб не было дубликатов в router
        if not known_routes.get(route_kwargs['url'], None):
            return RouteDrfs(**route_kwargs)

        known_mapping = known_routes[route_kwargs['url']]['mapping']
        for httpmethod in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']:
            if not isinstance(route_kwargs['mapping'].get(httpmethod, None), str):
                continue
            if isinstance(known_mapping.get(httpmethod, None), str):
                raise ImproperlyConfigured('Cannot map to url "%s" method "%s". Already exists. Try another url or method' % (
                    route_kwargs['url'],
                    httpmethod
                ))

        return RouteDrfs(**route_kwargs)


    def get_urls(self):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        ret = UrlPatternList()

        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_regex(viewset)
            routes = self.get_routes(viewset)

            for route in routes:

                # Only actions which actually exist on the viewset will be bound
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                # Build the url pattern
                if isinstance(route, RouteDrfs):
                    trailing_slash = route.trailing_slash
                    if trailing_slash is None:
                        trailing_slash = self.trailing_slash
                else:
                    trailing_slash = self.trailing_slash
                regex = route.url.format(
                    prefix=prefix,
                    lookup=lookup,
                    trailing_slash=trailing_slash
                )

                # If there is no prefix, the first part of the url is probably
                #   controlled by project's urls.py and the router is in an app,
                #   so a slash in the beginning will (A) cause Django to give
                #   warnings and (B) generate URLS that will require using '//'.
                if not prefix and regex[:2] == '^/':
                    regex = '^' + regex[2:]

                initkwargs = route.initkwargs.copy()
                if helpers.rest_framework_version >= (3,7,0):
                    initkwargs.update({'basename': basename})
                if helpers.rest_framework_version >= (3,8,0):
                    initkwargs.update({'detail': route.detail})

                view = viewset.as_view(mapping, **initkwargs)
                name = route.name.format(basename=basename)
                ret.append(re_path(regex, view, name=name))

        return ret



class DefaultRouter(BaseDefaultRouter):
    def register(self, prefix, viewset, base_name=None, basename=None):
        # old name base_name (drf<3.11), new - basename
        basename = base_name or basename
        if basename is None:
            if hasattr(self, 'get_default_basename'):
                # drf >= 3.11
                basename = self.get_default_basename(viewset)
            else:
                basename = self.get_default_base_name(viewset)
        self.registry.append((prefix, viewset, basename))
        # invalidate the urls cache
        if hasattr(self, '_urls'):
            del self._urls
