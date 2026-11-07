import common.fields
import django.db.models.deletion
from django.db import migrations, models


def align_sqlite_catalog_tables(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        for model_name in ["ServiceVersion", "Faq", "UnitService", "ServiceAgency", "NonWorkingDay"]:
            model = apps.get_model("catalog", model_name)
            schema_editor.delete_model(model)
            schema_editor.create_model(model)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    align_sqlite_catalog_tables,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.AlterModelOptions(
                    name="faq",
                    options={"ordering": ["-created_at"], "verbose_name": "FAQ", "verbose_name_plural": "FAQs"},
                ),
                migrations.RemoveField(
                    model_name="faq",
                    name="sort_order",
                ),
                migrations.RemoveField(
                    model_name="nonworkingday",
                    name="is_recurring",
                ),
                migrations.RemoveField(
                    model_name="serviceagency",
                    name="id",
                ),
                migrations.AlterUniqueTogether(
                    name="serviceversion",
                    unique_together={("service", "version")},
                ),
                migrations.RemoveField(
                    model_name="unitservice",
                    name="id",
                ),
                migrations.AddField(
                    model_name="nonworkingday",
                    name="scope",
                    field=models.CharField(default="national", max_length=20),
                ),
                migrations.AlterField(
                    model_name="faq",
                    name="service",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="serviceid",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalog.service",
                    ),
                ),
                migrations.AlterField(
                    model_name="serviceagency",
                    name="agency",
                    field=models.ForeignKey(
                        db_column="agencyid",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agency_services",
                        to="catalog.agency",
                    ),
                ),
                migrations.AlterField(
                    model_name="serviceagency",
                    name="service",
                    field=common.fields.CompositeKeyForeignKey(
                        db_column="serviceid",
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="service_agencies",
                        serialize=False,
                        to="catalog.service",
                    ),
                ),
                migrations.AlterField(
                    model_name="serviceversion",
                    name="created_by",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="createdby",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="accounts.internaluser",
                    ),
                ),
                migrations.AlterField(
                    model_name="serviceversion",
                    name="service",
                    field=models.ForeignKey(
                        db_column="serviceid",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="catalog.service",
                    ),
                ),
                migrations.AlterField(
                    model_name="unitservice",
                    name="service",
                    field=models.ForeignKey(
                        db_column="serviceid",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_units",
                        to="catalog.service",
                    ),
                ),
                migrations.AlterField(
                    model_name="unitservice",
                    name="unit",
                    field=common.fields.CompositeKeyForeignKey(
                        db_column="unitid",
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="unit_services",
                        serialize=False,
                        to="catalog.unit",
                    ),
                ),
                migrations.RemoveField(
                    model_name="serviceversion",
                    name="approved_at",
                ),
                migrations.RemoveField(
                    model_name="serviceversion",
                    name="approved_by",
                ),
                migrations.RemoveField(
                    model_name="serviceversion",
                    name="change_summary",
                ),
            ],
        ),
    ]
