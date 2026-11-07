from django.db import migrations, models


def align_sqlite_search_tables_forward(apps, schema_editor):
    """
    Em PostgreSQL: no-op (as tabelas físicas já possuem o schema final de baseline_0001_schema.sql).
    Em SQLite: adiciona sessionhash em searchquerylog e remove updatedat/deletedat de searchsynonym
    preservando integralmente os registros existentes.
    """
    if schema_editor.connection.vendor == "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        # 1. searchquerylog: adiciona coluna sessionhash sem perda de linhas
        cursor.execute("ALTER TABLE searchquerylog ADD COLUMN sessionhash varchar(64) NULL;")

        # 2. searchsynonym: remove updatedat e deletedat e aplica UNIQUE(term) preservando linhas
        cursor.execute(
            """
            CREATE TABLE searchsynonym__new (
                id char(32) NOT NULL PRIMARY KEY,
                term varchar(100) NOT NULL UNIQUE,
                synonyms text NOT NULL,
                isactive bool NOT NULL DEFAULT 1,
                createdat datetime NOT NULL
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO searchsynonym__new (id, term, synonyms, isactive, createdat)
            SELECT id, term, synonyms, isactive, createdat
            FROM searchsynonym;
            """
        )
        cursor.execute("DROP TABLE searchsynonym;")
        cursor.execute("ALTER TABLE searchsynonym__new RENAME TO searchsynonym;")


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    align_sqlite_search_tables_forward,
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
