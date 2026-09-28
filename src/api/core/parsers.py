from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class ObjectJSONParser(JSONParser):
    """Every write endpoint takes an object; a bare list, string or number
    would otherwise reach view code that assumes `.get()` exists.
    """

    def parse(self, stream, media_type=None, parser_context=None):
        data = super().parse(stream, media_type, parser_context)
        if not isinstance(data, dict):
            raise ParseError("Request body must be a JSON object.")
        return data
