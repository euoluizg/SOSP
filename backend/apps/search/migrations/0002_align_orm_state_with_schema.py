from django.db import IntegrityError, migrations, models, transaction


def align_sqlite_search_tables_forward(apps, schema_editor):
    """
    Em PostgreSQL: no-op (as tabelas físicas já possuem o schema final de baseline_0001_schema.sql).
    Em SQLite: adiciona sessionhash em searchquerylog e remove updatedat/deletedat de searchsynonym
    preservando integralmente os registros existentes e validando unicidade de 'term'.
    """
    if schema_editor.connection.vendor == "postgresql":
        return

    with transaction.atomic(using=schema_editor.connection.alias), schema_editor.connection.cursor() as cursor:
        # 1. searchquerylog: adiciona coluna sessionhash sem perda de linhas
        cursor.execute("SELECT id FROM searchquerylog ORDER BY id;")
        qlog_before = cursor.fetchall()
        cursor.execute("ALTER TABLE searchquerylog ADD COLUMN sessionhash varchar(64) NULL;")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_searchquerylog_term ON searchquerylog (term);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_searchquerylog_createdat ON searchquerylog (createdat);")
        cursor.execute("SELECT id FROM searchquerylog ORDER BY id;")
        qlog_after = cursor.fetchall()
        if qlog_after != qlog_before:
            raise IntegrityError("Divergência de registros após ALTER TABLE em searchquerylog.")

        # 2. searchsynonym: remove updatedat e deletedat e aplica UNIQUE(term) preservando linhas
        cursor.execute("SELECT id FROM searchsynonym ORDER BY id;")
        syn_before = cursor.fetchall()
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
        cursor.execute("SELECT id FROM searchsynonym ORDER BY id;")
        syn_after = cursor.fetchall()
        if syn_after != syn_before:
            raise IntegrityError("Divergência de registros após reconstrução de searchsynonym.")

        for tbl in ("searchquerylog", "searchsynonym"):
            cursor.execute(f"PRAGMA foreign_key_check({tbl});")
            fk_violations = cursor.fetchall()
            if fk_violations:
                raise IntegrityError(
                    f"Violação de integridade referencial (PRAGMA foreign_key_check) em '{tbl}': {fk_violations}"
                )


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
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
        migrations.RunPython(align_sqlite_search_tables_forward),
    ]
