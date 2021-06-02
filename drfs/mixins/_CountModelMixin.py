from rest_framework.response import Response

from drfs.decorators import action, drf_api_doc
from ..serializers.schema import CountQuerysetSerializer




class CountModelMixin(object):

    @drf_api_doc(response_serializer=CountQuerysetSerializer)
    @action(methods=['get'], detail=False)
    def count(self, request, *args, **kwargs):
        """
        Count instances of the model matched by where from the data source
        """
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'count': queryset.count()
        })
