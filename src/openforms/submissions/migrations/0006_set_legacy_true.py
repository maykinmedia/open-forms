# Generated by Django 4.2.11 on 2024-06-26 14:26

from django.db import migrations

from django.db.migrations.state import StateApps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def set_legacy_true(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Alter existing ``TemporaryFileUpload`` instances to have ``legacy`` set to ``True`` by default."""

    TemporaryFileUpload = apps.get_model("submissions", "TemporaryFileUpload")

    for file_upload in TemporaryFileUpload.objects.iterator():
        file_upload.legacy = True
        file_upload.save()


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0005_temporaryfileupload_legacy_and_more"),
    ]

    operations = [
        migrations.RunPython(
            set_legacy_true,
            migrations.RunPython.noop,
        ),
    ]
