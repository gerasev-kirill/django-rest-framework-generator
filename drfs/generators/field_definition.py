

class DjangoFieldDefinition:
    field_class = None
    args = []
    kwargs = {}
    def __init__(self, **kwargs):
        self.kwargs = kwargs
