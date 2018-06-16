


class ModelMixin(object):
    def say_hello(self):
        return "hello %s" % self.id


    def save(self, *args, **kwargs):
        if 'my_prop' in kwargs:
            self.string_field = kwargs['my_prop']
        super(ModelMixin, self).save()
