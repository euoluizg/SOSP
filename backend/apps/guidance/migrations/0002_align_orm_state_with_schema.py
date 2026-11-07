import django.utils.timezone
from django.db import migrations, models


def align_sqlite_guidance_tables(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        for model_name in ["GeneratedPdf", "GuidanceProgress"]:
            model = apps.get_model("guidance", model_name)
            schema_editor.delete_model(model)
            schema_editor.create_model(model)


class Migration(migrations.Migration):

    dependencies = [
        ("guidance", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    align_sqlite_guidance_tables,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="guidanceprogress",
                    name="created_at",
                ),
                migrations.AddField(
                    model_name="generatedpdf",
                    name="checklist_hash",
                    field=models.CharField(db_column="checklisthash", default="", max_length=64),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name="guidanceprogress",
                    name="completed_at",
                    field=models.DateTimeField(blank=True, db_column="completedat", null=True),
                ),
                migrations.AddField(
                    model_name="guidanceprogress",
                    name="started_at",
                    field=models.DateTimeField(
                        auto_now_add=True,
                        db_column="startedat",
                        default=django.utils.timezone.now,
                    ),
                    preserve_default=False,
                ),
            ],
        ),
    ]
