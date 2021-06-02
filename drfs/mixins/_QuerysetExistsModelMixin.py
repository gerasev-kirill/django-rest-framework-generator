from rest_framework.response import Response

from drfs.decorators import action, drf_api_doc
from ..serializers.schema import ExistsQuerysetSerializer






class QuerysetExistsModelMixin(object):

    @drf_api_doc(response_serializer=ExistsQuerysetSerializer)
    @action(methods=['get'], detail=False)
    def queryset_exists(self, request, *args, **kwargs):
        """
        Check whether a model queryset exists in the data source
        """
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'exists': queryset.exists()
        })
