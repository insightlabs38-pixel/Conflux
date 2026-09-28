import hashlib
import hmac

from django.conf import settings
from django.db import migrations, models


def _digest(token):
    key = f"conflux-session-token:{settings.SECRET_KEY}".encode()
    return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()


def hash_existing_tokens(apps, schema_editor):
    Session = apps.get_model("accounts", "Session")
    for session in Session.objects.all().iterator():
        session.token_digest = _digest(session.token)
        session.save(update_fields=["token_digest"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_oidc")]

    operations = [
        migrations.AddField(
            model_name="session",
            name="token_digest",
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.RunPython(hash_existing_tokens, migrations.RunPython.noop),
        migrations.RemoveField(model_name="session", name="token"),
        migrations.AlterField(
            model_name="session",
            name="token_digest",
            field=models.CharField(db_index=True, max_length=64, unique=True),
        ),
    ]
