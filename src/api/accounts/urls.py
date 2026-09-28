from django.urls import path

from . import oidc_views, views

urlpatterns = [
    path("login/", views.login, name="accounts-login"),
    path("logout/", views.logout, name="accounts-logout"),
    path("me/", views.me, name="accounts-me"),
    path("oidc/config/", oidc_views.oidc_config, name="accounts-oidc-config"),
    path("oidc/login/", oidc_views.oidc_login, name="accounts-oidc-login"),
    path("oidc/callback/", oidc_views.oidc_callback, name="accounts-oidc-callback"),
]
