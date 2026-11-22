from pathlib import Path
import re


def prepare_baseline_sql_for_django_transaction(raw_sql: str) -> str:
    """
    Remove de forma estritamente validada os delimitadores transacionais externos
    ('BEGIN;' no início e 'COMMIT;' no final) do arquivo baseline_0001_schema.sql,
    preservando integralmente todo o conteúdo DDL intermediário para que a execução
    seja controlada exclusivamente pela transação atômica do MigrationExecutor do Django.
    """
    lines = raw_sql.splitlines(keepends=True)

    first_stmt_idx = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            first_stmt_idx = idx
            break

    last_stmt_idx = None
    for idx in range(len(lines) - 1, -1, -1):
        stripped = lines[idx].strip()
        if stripped and not stripped.startswith("--"):
            last_stmt_idx = idx
            break

    if first_stmt_idx is None or last_stmt_idx is None:
        raise RuntimeError("Arquivo baseline_0001_schema.sql está vazio ou sem instruções DDL.")

    first_token = lines[first_stmt_idx].strip().upper()
    last_token = lines[last_stmt_idx].strip().upper()

    has_outer_begin = first_token == "BEGIN;"
    has_outer_commit = last_token == "COMMIT;"

    if has_outer_begin != has_outer_commit:
        raise RuntimeError(
            f"Delimitadores transacionais externos desbalanceados em baseline_0001_schema.sql: "
            f"início={lines[first_stmt_idx].strip()!r}, fim={lines[last_stmt_idx].strip()!r}."
        )

    if has_outer_begin and has_outer_commit:
        # Preserva comentários iniciais, todo o corpo DDL intermediário e quebras finais sem BEGIN;/COMMIT;
        expected_middle = "".join(lines[:first_stmt_idx] + lines[first_stmt_idx + 1 : last_stmt_idx] + lines[last_stmt_idx + 1 :])
        prepared_sql = expected_middle
    else:
        prepared_sql = raw_sql

    # Valida que fora de corpos PL/pgSQL ($$ ... $$) não resta nenhum comando de controle transacional
    sql_without_plpgsql_bodies = re.sub(r"\$\$.*?\$\$", "", prepared_sql, flags=re.DOTALL)
    forbidden_tx_match = re.search(
        r"(?im)^\s*(BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|START\s+TRANSACTION|END)\s*;",
        sql_without_plpgsql_bodies,
    )
    if forbidden_tx_match:
        raise RuntimeError(
            f"Comando transacional embutido proibido detectado no DDL da baseline: {forbidden_tx_match.group(0).strip()!r}"
        )

    return prepared_sql


def apply_baseline_sql(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        if not schema_editor.connection.in_atomic_block:
            raise RuntimeError(
                "Violação de atomicidade: a baseline PostgreSQL deve ser executada dentro de uma transação atômica do Django."
            )
        sql_file = Path(__file__).resolve().parent.parent.parent.parent / "common" / "sql" / "baseline_0001_schema.sql"
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
        prepared_sql = prepare_baseline_sql_for_django_transaction(sql_content)
        with schema_editor.connection.cursor() as cursor:
            cursor.cursor.execute(prepared_sql)
            cursor.cursor.execute("SELECT txid_current_if_assigned();")
            active_txid = cursor.cursor.fetchone()[0]
            if active_txid is None:
                raise RuntimeError(
                    "Violação transacional: o DDL da baseline sofreu COMMIT antecipado fora do controle do Django!"
                )
    else:
        for model_name in ["Gender", "InternalUser", "Citizen", "Session", "LoginAttempt", "PasswordReset"]:
            schema_editor.create_model(apps.get_model("accounts", model_name))

def reverse_baseline_sql(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.cursor.execute("""
                DROP TABLE IF EXISTS
                    auditDataSubjectRequest, auditEvent,
                    reportsExport,
                    notificationsPushSubscription, notificationsDelivery, notificationsPreference, notificationsTemplate,
                    feedbackQuestion, feedbackReviewReport, feedbackReview,
                    schedulingProtocolTransition, schedulingProtocolAttachment, schedulingProtocol, schedulingAppointment, schedulingSlot,
                    guidanceGeneratedPdf, guidanceProgress,
                    searchSynonym, searchQueryLog,
                    catalogServiceVersion, catalogFaq, catalogServiceDocument, catalogServiceStep,
                    catalogUnitService, catalogServiceAgency, catalogService,
                    catalognonworkingday, catalogUnitOpeningHour, catalogUnit, catalogAgency,
                    accountsPasswordReset, accountsLoginAttempt, accountsSession,
                    accountsInternalUser, accountsCitizen, accountsGender
                CASCADE;
                DROP VIEW IF EXISTS vw_schedulingSlotAvailability, vw_catalogServiceSearch CASCADE;
            """)
    else:
        for model_name in ["PasswordReset", "LoginAttempt", "Session", "Citizen", "InternalUser", "Gender"]:
            schema_editor.delete_model(apps.get_model("accounts", model_name))

# Generated by Django 5.1.15 on 2026-11-06 18:47

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Gender',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('name', models.CharField(max_length=40)),
                        ('sort_order', models.SmallIntegerField(db_column='sortorder', default=0)),
                        ('is_active', models.BooleanField(db_column='isactive', default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdat')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedat')),
                    ],
                    options={
                        'verbose_name': 'Gênero',
                        'verbose_name_plural': 'Gêneros',
                        'db_table': 'accountsgender',
                        'ordering': ['sort_order', 'name'],
                    },
                ),
                migrations.CreateModel(
                    name='InternalUser',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('cpf', models.CharField(max_length=11)),
                        ('full_name', models.CharField(db_column='fullname', max_length=120)),
                        ('email', models.CharField(max_length=200)),
                        ('registration_number', models.CharField(db_column='registrationnumber', max_length=20)),
                        ('agency_id', models.UUIDField(blank=True, db_column='agencyid', null=True)),
                        ('role', models.CharField(max_length=20)),
                        ('can_manage_catalog', models.BooleanField(db_column='canmanagecatalog', default=False)),
                        ('password_hash', models.CharField(db_column='passwordhash', max_length=255)),
                        ('must_change_password', models.BooleanField(db_column='mustchangepassword', default=True)),
                        ('is_active', models.BooleanField(db_column='isactive', default=True)),
                        ('last_login_at', models.DateTimeField(blank=True, db_column='lastloginat', null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdat')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedat')),
                        ('deleted_at', models.DateTimeField(blank=True, db_column='deletedat', null=True)),
                    ],
                    options={
                        'verbose_name': 'Usuário Interno',
                        'verbose_name_plural': 'Usuários Internos',
                        'db_table': 'accountsinternaluser',
                    },
                ),
                migrations.CreateModel(
                    name='LoginAttempt',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('cpf', models.CharField(max_length=11)),
                        ('ip_address', models.GenericIPAddressField(blank=True, db_column='ipaddress', null=True)),
                        ('was_successful', models.BooleanField(db_column='wassuccessful', default=False)),
                        ('attempted_at', models.DateTimeField(auto_now_add=True, db_column='attemptedat')),
                    ],
                    options={
                        'verbose_name': 'Tentativa de Login',
                        'verbose_name_plural': 'Tentativas de Login',
                        'db_table': 'accountsloginattempt',
                    },
                ),
                migrations.CreateModel(
                    name='Session',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('subject_type', models.CharField(db_column='subjecttype', max_length=20)),
                        ('subject_id', models.UUIDField(db_column='subjectid')),
                        ('token_hash', models.CharField(db_column='tokenhash', max_length=64)),
                        ('ip_address', models.GenericIPAddressField(blank=True, db_column='ipaddress', null=True)),
                        ('user_agent', models.CharField(blank=True, db_column='useragent', max_length=500, null=True)),
                        ('expires_at', models.DateTimeField(db_column='expiresat')),
                        ('revoked_at', models.DateTimeField(blank=True, db_column='revokedat', null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdat')),
                    ],
                    options={
                        'verbose_name': 'Sessão',
                        'verbose_name_plural': 'Sessões',
                        'db_table': 'accountssession',
                    },
                ),
                migrations.CreateModel(
                    name='Citizen',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('cpf', models.CharField(max_length=11)),
                        ('full_name', models.CharField(db_column='fullname', max_length=120)),
                        ('birth_date', models.DateField(db_column='birthdate')),
                        ('email', models.CharField(max_length=200)),
                        ('phone', models.CharField(max_length=11)),
                        ('password_hash', models.TextField(db_column='passwordhash')),
                        ('password_salt', models.TextField(db_column='passwordsalt')),
                        ('recovery_code_hash', models.TextField(blank=True, db_column='recoverycodehash', null=True)),
                        ('recovery_code_expires_at', models.DateTimeField(blank=True, db_column='recoverycodeexpiresat', null=True)),
                        ('login_attempts', models.IntegerField(db_column='loginattempts', default=0)),
                        ('blocked_until', models.DateTimeField(blank=True, db_column='blockeduntil', null=True)),
                        ('is_pcd', models.BooleanField(db_column='ispcd', default=False)),
                        ('disability_description', models.CharField(blank=True, db_column='disabilitydescription', max_length=120, null=True)),
                        ('mother_name', models.CharField(db_column='mothername', max_length=120)),
                        ('father_name', models.CharField(blank=True, db_column='fathername', max_length=120, null=True)),
                        ('zip_code', models.CharField(db_column='zipcode', max_length=8)),
                        ('street', models.CharField(max_length=120)),
                        ('neighborhood', models.CharField(max_length=80)),
                        ('city', models.CharField(max_length=80)),
                        ('state', models.CharField(max_length=2)),
                        ('address_number', models.CharField(db_column='addressnumber', max_length=10)),
                        ('address_complement', models.CharField(blank=True, db_column='addresscomplement', max_length=60, null=True)),
                        ('avatar_url', models.CharField(blank=True, db_column='avatarurl', max_length=500, null=True)),
                        ('govbr_subject_id', models.CharField(blank=True, db_column='govbrsubjectid', max_length=255, null=True)),
                        ('email_verified_at', models.DateTimeField(blank=True, db_column='emailverifiedat', null=True)),
                        ('last_login_at', models.DateTimeField(blank=True, db_column='lastloginat', null=True)),
                        ('is_active', models.BooleanField(db_column='isactive', default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdat')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedat')),
                        ('deleted_at', models.DateTimeField(blank=True, db_column='deletedat', null=True)),
                        ('gender', models.ForeignKey(db_column='genderid', on_delete=django.db.models.deletion.PROTECT, to='accounts.gender')),
                    ],
                    options={
                        'verbose_name': 'Cidadão',
                        'verbose_name_plural': 'Cidadãos',
                        'db_table': 'accountscitizen',
                    },
                ),
                migrations.CreateModel(
                    name='PasswordReset',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('code_hash', models.CharField(db_column='codehash', max_length=255)),
                        ('expires_at', models.DateTimeField(db_column='expiresat')),
                        ('used_at', models.DateTimeField(blank=True, db_column='usedat', null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdat')),
                        ('internal_user', models.ForeignKey(db_column='internaluserid', on_delete=django.db.models.deletion.CASCADE, to='accounts.internaluser')),
                    ],
                    options={
                        'verbose_name': 'Redefinição de Senha',
                        'verbose_name_plural': 'Redefinições de Senha',
                        'db_table': 'accountspasswordreset',
                    },
                ),
            ],
        ),
        migrations.RunPython(apply_baseline_sql, reverse_baseline_sql),
    ]
