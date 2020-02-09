
from django.core.exceptions import ImproperlyConfigured
from rest_framework.routers import SimpleRouter as BaseSimpleRouter, Route, DynamicDetailRoute, DynamicListRoute
from rest_framework.routers import flatten, replace_methodname



class SimpleRouter(BaseSimpleRouter):
    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of the Route namedtuple.
        """
        # converting to list as iterables are good for one pass, known host needs to be checked again and again for
        # different functions.
        known_actions = list(flatten([route.mapping.values() for route in self.routes if isinstance(route, Route)]))
        # Determine any `@detail_route` or `@list_route` decorated methods on the viewset
        detail_routes = []
        list_routes = []
        for methodname in dir(viewset):
            attr = getattr(viewset, methodname)
            httpmethods = getattr(attr, 'bind_to_methods', None)
            detail = getattr(attr, 'detail', True)
            if httpmethods:
                # checking method names against the known actions list
                if methodname in known_actions:
                    raise ImproperlyConfigured('Cannot use @detail_route or @list_route '
                                               'decorators on method "%s" '
                                               'as it is an existing route' % methodname)
                httpmethods = [method.lower() for method in httpmethods]
                if detail:
                    detail_routes.append((httpmethods, methodname))
                else:
                    list_routes.append((httpmethods, methodname))

        def _get_dynamic_routes(route, dynamic_routes):
            ret = {}
            for httpmethods, methodname in dynamic_routes:
                method_kwargs = getattr(viewset, methodname).kwargs
                initkwargs = route.initkwargs.copy()
                initkwargs.update(method_kwargs)
                url_path = initkwargs.pop("url_path", None) or methodname
                url_name = initkwargs.pop("url_name", None) or url_path
                full_url = replace_methodname(route.url, url_path)
                if ret.get(full_url, None):
                    for httpmethod in httpmethods:
                        if ret[full_url]['mapping'].get(httpmethod):
                            raise ImproperlyConfigured('Cannot map to url "%s" method "%s". Already exists. Try another url or method' % (
                                full_url,
                                httpmethod
                            ))
                        ret[full_url]['mapping'][httpmethod] = methodname
                else:
                    ret[full_url] = {
                        'url': full_url,
                        'mapping': {httpmethod: methodname for httpmethod in httpmethods},
                        'name': replace_methodname(route.name, url_name),
                        'initkwargs': initkwargs,
                    }
            return [Route(**params) for fulr, params in ret.items()]


            ret = []
            for httpmethods, methodname in dynamic_routes:
                method_kwargs = getattr(viewset, methodname).kwargs
                initkwargs = route.initkwargs.copy()
                initkwargs.update(method_kwargs)
                url_path = initkwargs.pop("url_path", None) or methodname
                url_name = initkwargs.pop("url_name", None) or url_path
                ret.append(Route(
                    url=replace_methodname(route.url, url_path),
                    mapping={httpmethod: methodname for httpmethod in httpmethods},
                    name=replace_methodname(route.name, url_name),
                    initkwargs=initkwargs,
                ))
            if 'CmsBlogEntry' in viewset.__name__:
                print(ret)
                print()
            return ret

        ret = []
        for route in self.routes:
            if isinstance(route, DynamicDetailRoute):
                # Dynamic detail routes (@detail_route decorator)
                ret += _get_dynamic_routes(route, detail_routes)
            elif isinstance(route, DynamicListRoute):
                # Dynamic list routes (@list_route decorator)
                ret += _get_dynamic_routes(route, list_routes)
            else:
                # Standard route
                ret.append(route)

        return ret
