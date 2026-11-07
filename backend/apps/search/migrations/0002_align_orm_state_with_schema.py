from django.db import migrations, models


def align_sqlite_search_tables(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        for model_name in ["Synonym", "QueryLog"]:
            model = apps.get_model("search", model_name)
            schema_editor.delete_model(model)
            schema_editor.create_model(model)


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    align_sqlite_search_tables,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="synonym",
                    name="deleted_at",
                ),
                migrations.RemoveField(
                    model_name="synonym",
                    name="updated_at",
                ),
                migrations.AddField(
                    model_name="querylog",
                    name="session_hash",
                    field=models.CharField(blank=True, db_column="sessionhash", max_length=64, null=True),
                ),
                migrations.AlterField(
                    model_name="synonym",
                    name="term",
                    field=models.CharField(max_length=100, unique=True),
                ),
            ],
        ),
    ]
