from celery import shared_task

from .models import Artifact
from .validators import validate_artifact


@shared_task
def validate_artifact_task(artifact_public_id):
    artifact = Artifact.objects.get(public_id=artifact_public_id)
    evidence = validate_artifact(artifact)
    return str(evidence.public_id)
