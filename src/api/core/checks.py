"""The startup conformance check for extension manifests (EXTENSION_MANIFEST).

Errors fail `manage.py check` (and so `migrate` and `runserver`): a manifest that claims what is not
registered, a registered entry nobody may claim twice, an unsupported API version or an unresolved
requirement means the deployment's extensions are inconsistent. An entry registered without any
manifest is only a warning, so a feature in progress does not block the rest.
"""

from django.core import checks

from . import manifest


@checks.register(checks.Tags.compatibility)
def extension_manifests(app_configs, **kwargs):
    found = []
    for item in manifest.check():
        level = checks.Error if item["severity"] == "error" else checks.Warning
        owner = f"[{item['manifest']}] " if item["manifest"] else ""
        found.append(level(f"{owner}{item['message']}", id=f"core.manifest.{item['code']}"))
    return found
