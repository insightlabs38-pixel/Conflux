import re

from drf_spectacular.openapi import AutoSchema


class ConfluxAutoSchema(AutoSchema):
    def get_operation_id(self):
        path = re.sub(r"[^a-zA-Z0-9]+", "_", self.path).strip("_").lower()
        return f"{self.method.lower()}_{path}"
