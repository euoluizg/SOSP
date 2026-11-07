import common.fields
import django.db.models.deletion
from django.db import migrations, models


def align_sqlite_catalog_tables_forward(apps, schema_editor):
    """
    Em PostgreSQL: no-op (as tabelas físicas já nascem com o schema final em baseline_0001_schema.sql).
    Em SQLite: migra a estrutura das 5 tabelas preservando 100% dos registros e relacionamentos existentes
    e definindo chave primária composta real em catalogserviceagency e catalogunitservice.
    """
    if schema_editor.connection.vendor == "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        # 1. catalognonworkingday: substitui isrecurring por scope preservando linhas existentes
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
        cursor.execute("CREATE INDEX catalognonworkingday_unitid_idx ON catalognonworkingday (unitid);")

        # 2. catalogserviceagency: remove coluna artificial id, define PRIMARY KEY composta (serviceid, agencyid)
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
            INSERT OR IGNORE INTO catalogserviceagency__new (serviceid, agencyid)
            SELECT serviceid, agencyid
            FROM catalogserviceagency;
            """
        )
        cursor.execute("DROP TABLE catalogserviceagency;")
        cursor.execute("ALTER TABLE catalogserviceagency__new RENAME TO catalogserviceagency;")
        cursor.execute("CREATE INDEX idxCatalogServiceAgencyAgency ON catalogserviceagency (agencyid);")

        # 3. catalogunitservice: remove coluna artificial id, define PRIMARY KEY composta (unitid, serviceid)
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
            INSERT OR IGNORE INTO catalogunitservice__new (unitid, serviceid, isactive, createdat)
            SELECT unitid, serviceid, isactive, createdat
            FROM catalogunitservice;
            """
        )
        cursor.execute("DROP TABLE catalogunitservice;")
        cursor.execute("ALTER TABLE catalogunitservice__new RENAME TO catalogunitservice;")
        cursor.execute("CREATE INDEX idxCatalogUnitServiceService ON catalogunitservice (serviceid);")

        # 4. catalogfaq: remove sortorder e alinha FK serviceid ON DELETE CASCADE preservando linhas
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
        cursor.execute("CREATE INDEX catalogfaq_serviceid_idx ON catalogfaq (serviceid);")

        # 5. catalogserviceversion: remove changesummary/approvedby/approvedat, alinha FK createdby e UNIQUE (serviceid, version)
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
            SELECT id, version, snapshot, createdat,
                   CASE WHEN createdby IN (SELECT id FROM accountsinternaluser) THEN createdby ELSE NULL END,
                   serviceid
            FROM catalogserviceversion;
            """
        )
        cursor.execute("DROP TABLE catalogserviceversion;")
        cursor.execute("ALTER TABLE catalogserviceversion__new RENAME TO catalogserviceversion;")
        cursor.execute("CREATE INDEX catalogserviceversion_serviceid_idx ON catalogserviceversion (serviceid);")
        cursor.execute("CREATE INDEX catalogserviceversion_createdby_idx ON catalogserviceversion (createdby);")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    align_sqlite_catalog_tables_forward,
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
