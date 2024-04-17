from jinja2.ext import Extension


class RequestPathExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["get_base_path"] = self.get_base_path

    def get_base_path(self, request):
        return request.url.path.rsplit("/", 1)[0]
