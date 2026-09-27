from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CookieAndBearerScheme(OpenApiAuthenticationExtension):
    target_class = "accounts.authentication.CookieSessionAuthentication"
    name = ["sessionCookie", "scopedBearer"]

    def get_security_requirement(self, auto_schema):
        return [{"sessionCookie": []}, {"scopedBearer": []}]

    def get_security_definition(self, auto_schema):
        return [
            {"type": "apiKey", "in": "cookie", "name": "session"},
            {"type": "http", "scheme": "bearer"},
        ]


class CookieOnlyScheme(OpenApiAuthenticationExtension):
    target_class = "accounts.authentication.CookieOnlyAuthentication"
    name = "humanSessionCookie"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "cookie", "name": "session"}
