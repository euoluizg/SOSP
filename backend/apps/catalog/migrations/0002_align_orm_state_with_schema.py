import common.fields
import django.db.models.deletion
from django.db import IntegrityError, migrations, models, transaction


def _verify_table_counts_and_keys(cursor, table_name: str, key_expr: str, before_keys: list):
    cursor.execute(f"SELECT {key_expr} FROM {table_name} ORDER BY {key_expr};")
    after_keys = cursor.fetchall()
    if len(after_keys) != len(before_keys) or after_keys != before_keys:
        raise IntegrityError(
            f"Falha de integridade na reconstrução de '{table_name}': "
            f"antes={len(before_keys)} registros, depois={len(after_keys)} registros."
        )


def align_sqlite_catalog_tables_forward(apps, schema_editor):
    """
    Em PostgreSQL: no-op (as tabelas físicas já nascem com o schema final em baseline_0001_schema.sql).
    Em SQLite: migra a estrutura das 5 tabelas sem perda silenciosa (sem INSERT OR IGNORE),
    validando contagens, identidade dos registros e PRAGMA foreign_key_check.
    """
    if schema_editor.connection.vendor == "postgresql":
        return

    with transaction.atomic(using=schema_editor.connection.alias), schema_editor.connection.cursor() as cursor:
        # 1. catalognonworkingday: substitui isrecurring por scope preservando linhas existentes
        cursor.execute("SELECT id FROM catalognonworkingday ORDER BY id;")
        nwd_before = cursor.fetchall()
        cursor.execute(
            """
            CREATE TABLE catalognonworkingday__new (
                id char(32) NOT NULL PRIMARY KEY,
                daydate date NOT NULL,
                description varchar(120) NOT NULL,
                scope varchar(20) NOT NULL DEFAULT 'national',
                createdat datetime NOT NULL,
                unitid char(32) NULL REFERENCES catalogunit(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO catalognonworkingday__new (id, daydate, description, scope, createdat, unitid)
            SELECT id, daydate, description,
                   CASE WHEN unitid IS NOT NULL THEN 'unit' ELSE 'national' END,
                   createdat, unitid
            FROM catalognonworkingday;
            """
        )
        cursor.execute("DROP TABLE catalognonworkingday;")
        cursor.execute("ALTER TABLE catalognonworkingday__new RENAME TO catalognonworkingday;")
        cursor.execute("CREATE INDEX idx_nonworkingday_unitid ON catalognonworkingday (unitid);")
        cursor.execute("CREATE INDEX idx_nonworkingday_daydate ON catalognonworkingday (daydate);")
        _verify_table_counts_and_keys(cursor, "catalognonworkingday", "id", nwd_before)

        # 2. catalogserviceagency: remove coluna artificial id, define PRIMARY KEY composta (serviceid, agencyid)
        # Usa INSERT INTO estrito (sem OR IGNORE): duplicatas provocam IntegrityError e rollback transacional.
        cursor.execute("SELECT serviceid, agencyid FROM catalogserviceagency ORDER BY serviceid, agencyid;")
        sa_before = cursor.fetchall()
        cursor.execute(
            """
            CREATE TABLE catalogserviceagency__new (
                serviceid char(32) NOT NULL REFERENCES catalogservice(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                agencyid char(32) NOT NULL REFERENCES catalogagency(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                PRIMARY KEY (serviceid, agencyid)
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO catalogserviceagency__new (serviceid, agencyid)
            SELECT serviceid, agencyid
            FROM catalogserviceagency;
            """
        )
        cursor.execute("DROP TABLE catalogserviceagency;")
        cursor.execute("ALTER TABLE catalogserviceagency__new RENAME TO catalogserviceagency;")
        cursor.execute("CREATE INDEX idx_serviceagency_agencyid ON catalogserviceagency (agencyid);")
        _verify_table_counts_and_keys(cursor, "catalogserviceagency", "serviceid, agencyid", sa_before)

        # 3. catalogunitservice: remove coluna artificial id, define PRIMARY KEY composta (unitid, serviceid)
        # Usa INSERT INTO estrito (sem OR IGNORE): duplicatas provocam IntegrityError e rollback transacional.
        cursor.execute("SELECT unitid, serviceid FROM catalogunitservice ORDER BY unitid, serviceid;")
        us_before = cursor.fetchall()
        cursor.execute(
            """
            CREATE TABLE catalogunitservice__new (
                unitid char(32) NOT NULL REFERENCES catalogunit(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                serviceid char(32) NOT NULL REFERENCES catalogservice(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                isactive bool NOT NULL DEFAULT 1,
                createdat datetime NOT NULL,
                PRIMARY KEY (unitid, serviceid)
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO catalogunitservice__new (unitid, serviceid, isactive, createdat)
            SELECT unitid, serviceid, isactive, createdat
            FROM catalogunitservice;
            """
        )
        cursor.execute("DROP TABLE catalogunitservice;")
        cursor.execute("ALTER TABLE catalogunitservice__new RENAME TO catalogunitservice;")
        cursor.execute("CREATE INDEX idx_unitservice_serviceid ON catalogunitservice (serviceid);")
        _verify_table_counts_and_keys(cursor, "catalogunitservice", "unitid, serviceid", us_before)

        # 4. catalogfaq: remove sortorder e alinha FK serviceid ON DELETE CASCADE preservando linhas
        cursor.execute("SELECT id FROM catalogfaq ORDER BY id;")
        faq_before = cursor.fetchall()
        cursor.execute(
            """
            CREATE TABLE catalogfaq__new (
                id char(32) NOT NULL PRIMARY KEY,
                category varchar(30) NULL,
                question varchar(300) NOT NULL,
                answer varchar(2000) NOT NULL,
                isactive bool NOT NULL DEFAULT 1,
                createdat datetime NOT NULL,
                updatedat datetime NOT NULL,
                serviceid char(32) NULL REFERENCES catalogservice(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO catalogfaq__new (id, category, question, answer, isactive, createdat, updatedat, serviceid)
            SELECT id, category, question, answer, isactive, createdat, updatedat, serviceid
            FROM catalogfaq;
            """
        )
        cursor.execute("DROP TABLE catalogfaq;")
        cursor.execute("ALTER TABLE catalogfaq__new RENAME TO catalogfaq;")
        cursor.execute("CREATE INDEX idx_faq_serviceid ON catalogfaq (serviceid);")
        cursor.execute("CREATE INDEX idx_faq_category ON catalogfaq (category);")
        _verify_table_counts_and_keys(cursor, "catalogfaq", "id", faq_before)

        # 5. catalogserviceversion: remove changesummary/approvedby/approvedat, alinha FK createdby e UNIQUE (serviceid, version)
        cursor.execute("SELECT id FROM catalogserviceversion ORDER BY id;")
        sv_before = cursor.fetchall()
        cursor.execute(
            """
            CREATE TABLE catalogserviceversion__new (
                id char(32) NOT NULL PRIMARY KEY,
                version integer NOT NULL,
                snapshot text NOT NULL CHECK ((JSON_VALID("snapshot") OR "snapshot" IS NULL)),
                createdat datetime NOT NULL,
                createdby char(32) NULL REFERENCES accountsinternaluser(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
                serviceid char(32) NOT NULL REFERENCES catalogservice(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                UNIQUE (serviceid, version)
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO catalogserviceversion__new (id, version, snapshot, createdat, createdby, serviceid)
            SELECT id, version, snapshot, createdat, createdby, serviceid
            FROM catalogserviceversion;
            """
        )
        cursor.execute("DROP TABLE catalogserviceversion;")
        cursor.execute("ALTER TABLE catalogserviceversion__new RENAME TO catalogserviceversion;")
        cursor.execute("CREATE INDEX idx_serviceversion_serviceid ON catalogserviceversion (serviceid);")
        cursor.execute("CREATE INDEX idx_serviceversion_createdby ON catalogserviceversion (createdby);")
        _verify_table_counts_and_keys(cursor, "catalogserviceversion", "id", sv_before)

        # Valida integridade referencial de todas as tabelas reconstruídas no módulo catalog
        for tbl in (
            "catalognonworkingday",
            "catalogserviceagency",
            "catalogunitservice",
            "catalogfaq",
            "catalogserviceversion",
        ):
            cursor.execute(f"PRAGMA foreign_key_check({tbl});")
            fk_violations = cursor.fetchall()
            if fk_violations:
                raise IntegrityError(
                    f"Violação de integridade referencial (PRAGMA foreign_key_check) em '{tbl}': {fk_violations}"
                )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
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
        migrations.RunPython(align_sqlite_catalog_tables_forward),
    ]
