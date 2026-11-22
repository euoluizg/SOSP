import django.utils.timezone
from django.db import IntegrityError, migrations, models, transaction


def align_sqlite_guidance_tables_forward(apps, schema_editor):
    """
    Em PostgreSQL: no-op (as tabelas físicas já possuem o schema final de baseline_0001_schema.sql).
    Em SQLite: migra guidanceprogress (createdat -> startedat + completedat) e adiciona checklisthash
    em guidancegeneratedpdf preservando 100% dos registros e relacionamentos existentes.
    """
    if schema_editor.connection.vendor == "postgresql":
        return

    with transaction.atomic(using=schema_editor.connection.alias), schema_editor.connection.cursor() as cursor:
        # 1. guidanceprogress: migra createdat -> startedat e adiciona completedat preservando linhas
        cursor.execute("SELECT id FROM guidanceprogress ORDER BY id;")
        gp_before = cursor.fetchall()
        cursor.execute(
            """
            CREATE TABLE guidanceprogress__new (
                id char(32) NOT NULL PRIMARY KEY,
                checkeddocumentids text NOT NULL,
                startedat datetime NOT NULL,
                completedat datetime NULL,
                updatedat datetime NOT NULL,
                citizenid char(32) NOT NULL REFERENCES accountscitizen(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                serviceid char(32) NOT NULL REFERENCES catalogservice(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                UNIQUE (citizenid, serviceid)
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO guidanceprogress__new (
                id, checkeddocumentids, startedat, completedat, updatedat, citizenid, serviceid
            )
            SELECT
                id,
                checkeddocumentids,
                COALESCE(createdat, updatedat, CURRENT_TIMESTAMP),
                NULL,
                updatedat,
                citizenid,
                serviceid
            FROM guidanceprogress;
            """
        )
        cursor.execute("DROP TABLE guidanceprogress;")
        cursor.execute("ALTER TABLE guidanceprogress__new RENAME TO guidanceprogress;")
        cursor.execute("CREATE INDEX idx_guidanceprogress_citizenid ON guidanceprogress (citizenid);")
        cursor.execute("CREATE INDEX idx_guidanceprogress_serviceid ON guidanceprogress (serviceid);")
        cursor.execute("SELECT id FROM guidanceprogress ORDER BY id;")
        gp_after = cursor.fetchall()
        if gp_after != gp_before:
            raise IntegrityError("Divergência de registros após reconstrução de guidanceprogress.")

        # 2. guidancegeneratedpdf: adiciona checklisthash preservando todas as linhas existentes
        cursor.execute("SELECT id FROM guidancegeneratedpdf ORDER BY id;")
        pdf_before = cursor.fetchall()
        cursor.execute(
            """
            CREATE TABLE guidancegeneratedpdf__new (
                id char(32) NOT NULL PRIMARY KEY,
                fileurl varchar(500) NOT NULL,
                checklisthash varchar(64) NOT NULL,
                expiresat datetime NOT NULL,
                createdat datetime NOT NULL,
                citizenid char(32) NOT NULL REFERENCES accountscitizen(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                serviceid char(32) NOT NULL REFERENCES catalogservice(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO guidancegeneratedpdf__new (
                id, fileurl, checklisthash, expiresat, createdat, citizenid, serviceid
            )
            SELECT
                id,
                fileurl,
                'legacy_migrated_hash',
                expiresat,
                createdat,
                citizenid,
                serviceid
            FROM guidancegeneratedpdf;
            """
        )
        cursor.execute("DROP TABLE guidancegeneratedpdf;")
        cursor.execute("ALTER TABLE guidancegeneratedpdf__new RENAME TO guidancegeneratedpdf;")
        cursor.execute("CREATE INDEX idx_guidancepdf_citizenid ON guidancegeneratedpdf (citizenid);")
        cursor.execute("CREATE INDEX idx_guidancepdf_serviceid ON guidancegeneratedpdf (serviceid);")
        cursor.execute("CREATE INDEX idx_guidancepdf_expiresat ON guidancegeneratedpdf (expiresat);")
        cursor.execute("SELECT id FROM guidancegeneratedpdf ORDER BY id;")
        pdf_after = cursor.fetchall()
        if pdf_after != pdf_before:
            raise IntegrityError("Divergência de registros após reconstrução de guidancegeneratedpdf.")

        for tbl in ("guidanceprogress", "guidancegeneratedpdf"):
            cursor.execute(f"PRAGMA foreign_key_check({tbl});")
            fk_violations = cursor.fetchall()
            if fk_violations:
                raise IntegrityError(
                    f"Violação de integridade referencial (PRAGMA foreign_key_check) em '{tbl}': {fk_violations}"
                )


class Migration(migrations.Migration):

    dependencies = [
        ("guidance", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
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
        migrations.RunPython(align_sqlite_guidance_tables_forward),
    ]
