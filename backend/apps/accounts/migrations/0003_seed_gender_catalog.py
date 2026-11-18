from django.db import migrations


def seed_gender_catalog(apps, schema_editor):
    """Insere as referências oficiais do cadastro descritas no Pilar 4."""
    gender = apps.get_model("accounts", "Gender")
    catalog = gender.objects.using(schema_editor.connection.alias)

    for sort_order, name in enumerate(
        ("Feminino", "Masculino", "Não binário", "Outro", "Prefiro não informar"),
        start=1,
    ):
        catalog.get_or_create(name=name, defaults={"sort_order": sort_order})


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_add_gender_description_and_unit_to_accounts")]

    # Preserva referências que já podem estar vinculadas a cidadãos.
    operations = [migrations.RunPython(seed_gender_catalog, migrations.RunPython.noop)]
