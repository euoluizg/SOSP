from django.db import migrations, models


def align_accounts_schema_forward(apps, schema_editor):
    """
    Aplica incrementalmente as colunas e constraints de schema:
    1. genderDescription em accountsCitizen.
    2. unitId em accountsInternalUser.
    3. Atualização e harmonização de constraints de accountsInternalUser e accountsSession
       (removendo constraints legadas incompatíveis e garantindo compatibilidade com gestor, superadmin e hífens em matrículas).
    Preserva idempotência tanto em PostgreSQL quanto em SQLite.
    """
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                """
                ALTER TABLE accountsCitizen
                    ADD COLUMN IF NOT EXISTS genderDescription varchar(120);

                ALTER TABLE accountsInternalUser
                    ADD COLUMN IF NOT EXISTS unitId uuid;

                CREATE INDEX IF NOT EXISTS idxAccountsInternalUserUnit
                    ON accountsInternalUser (unitId);

                -- Remove constraints legadas do baseline antigo se existirem
                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalUserRole;
                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalUserRegistration;
                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalUserCpf;

                -- Harmoniza e garante constraints oficiais de accountsInternalUser de forma idempotente
                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalRole;
                ALTER TABLE accountsInternalUser ADD CONSTRAINT chkAccountsInternalRole
                    CHECK (role IN ('superadmin', 'admin', 'gestor', 'server', 'manager', 'servant', 'administrator'));

                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalRegistration;
                ALTER TABLE accountsInternalUser ADD CONSTRAINT chkAccountsInternalRegistration
                    CHECK (registrationNumber ~ '^[A-Za-z0-9-]{1,20}$');

                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalCpf;
                ALTER TABLE accountsInternalUser ADD CONSTRAINT chkAccountsInternalCpf
                    CHECK (cpf ~ '^[0-9]{11}$');

                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalEmail;
                ALTER TABLE accountsInternalUser ADD CONSTRAINT chkAccountsInternalEmail
                    CHECK (email ~* '^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$');

                ALTER TABLE accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalName;
                ALTER TABLE accountsInternalUser ADD CONSTRAINT chkAccountsInternalName
                    CHECK (char_length(fullName) >= 3);

                -- Harmoniza constraint de accountsSession de forma idempotente
                ALTER TABLE accountsSession DROP CONSTRAINT IF EXISTS chkAccountsSessionSubjectType;
                ALTER TABLE accountsSession DROP CONSTRAINT IF EXISTS chkAccountsSessionSubject;
                ALTER TABLE accountsSession ADD CONSTRAINT chkAccountsSessionSubject
                    CHECK (subjectType IN ('citizen', 'internal'));
                """
            )
        else:
            # SQLite: adiciona colunas caso ainda não existam no schema da tabela
            cursor.execute("PRAGMA table_info(accountscitizen);")
            citizen_cols = [row[1] for row in cursor.fetchall()]
            if "genderdescription" not in citizen_cols:
                cursor.execute("ALTER TABLE accountscitizen ADD COLUMN genderdescription varchar(120) NULL;")

            cursor.execute("PRAGMA table_info(accountsinternaluser);")
            internal_cols = [row[1] for row in cursor.fetchall()]
            if "unitid" not in internal_cols:
                cursor.execute("ALTER TABLE accountsinternaluser ADD COLUMN unitid char(32) NULL;")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="citizen",
                    name="gender_description",
                    field=models.CharField(
                        blank=True,
                        db_column="genderdescription",
                        max_length=120,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name="internaluser",
                    name="unit_id",
                    field=models.UUIDField(
                        blank=True,
                        db_column="unitid",
                        null=True,
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.RunPython(align_accounts_schema_forward, reverse_code=migrations.RunPython.noop),
    ]

