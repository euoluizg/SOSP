# Pilar 5 — Engenharia, DevOps e Operação

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 31/10/2026 · **Status:** Em revisão
> **Autores:** Equipe de Engenharia de Software — CESMAC
> **Documentos irmãos:** [Pilar 1](01-product-specs.md) · [Pilar 2](02-design-ux.md) · [Pilar 3](03-architecture.md) · [Pilar 4](04-data-api.md)
> **Documentos complementares:** [CONTRIBUTING](../CONTRIBUTING.md) · [CHANGELOG](../CHANGELOG.md) · [ADR-004 — Git Flow](adr/ADR-004-git-flow-simplificado.md) · [ADR-007 — Feature flags](adr/ADR-007-feature-flags.md) · [ADR-008 — Supabase](adr/ADR-008-supabase-postgresql-gerenciado.md) · [Glossário](glossario.md)
> **Artefatos operacionais:** [`schema.sql`](database/schema.sql) · [`openapi.yaml`](api/openapi.yaml) · [`.env.example`](../.env.example)

---

## Sumário

1. [Onboarding](#1-onboarding)
2. [Configuração e segredos](#2-configuração-e-segredos)
3. [Padrões de código e Git](#3-padrões-de-código-e-git)
4. [Estratégia de testes](#4-estratégia-de-testes)
5. [CI/CD](#5-cicd)
6. [Observabilidade](#6-observabilidade)
7. [Runbook de operação](#7-runbook-de-operação)
8. [Backup e restore](#8-backup-e-restore)
9. [Postmortem sem culpa](#9-postmortem-sem-culpa)
10. [Feature flags e ambientes](#10-feature-flags-e-ambientes)
11. [Rastreabilidade e definição de pronto operacional](#11-rastreabilidade-e-definição-de-pronto-operacional)

---

## 1. Onboarding

O objetivo desta seção é que uma pessoa nova saia do zero e veja a jornada completa — busca, ficha, guia, agendamento e protocolo — rodando na máquina local em menos de 30 minutos, sem pedir ajuda.

### 1.1 Pré-requisitos

| Ferramenta | Versão mínima | Como verificar | Observação |
|---|---|---|---|
| Git | 2.40 | `git --version` | — |
| Python | 3.12 | `python3.12 --version` | 3.13 funciona, mas o alvo é 3.12 |
| Node.js | 22 LTS | `node --version` | Next.js 15 exige Node 18.18+ |
| npm | 10 | `npm --version` | Vem com o Node |
| Docker | 24 | `docker --version` | Precisa do daemon rodando |
| Docker Compose | v2 | `docker compose version` | Comando é `docker compose`, sem hífen |
| PostgreSQL client | 17 | `psql --version` | Necessário para os comandos de backup e restore; a major version acompanha o servidor |
| Make | 3.81 | `make --version` | Opcional; os comandos também funcionam sem Make |

**Regra:** nenhuma dependência de serviço proprietário no núcleo. Tudo que o sistema precisa para rodar localmente sobe em contêineres ou é open source (RNF-11).

### 1.2 Clonar e entender a árvore

```bash
git clone https://github.com/<org>/sosp.git
cd sosp
```

```text
sosp/
├── .github/                  # workflows, templates de issue/PR e CODEOWNERS
├── backend/                  # API Django, back-office e workers
├── portal/                   # Next.js 15
├── docs/                     # esta documentação
├── fixtures/                 # dados de demonstração
├── scripts/                  # fronteiras, identificadores, deploy, DLQ
├── deploy/                   # compose de produção e manifests
├── docker-compose.yml        # infraestrutura de desenvolvimento
├── .env.example              # catálogo canônico de variáveis
├── Makefile
├── CONTRIBUTING.md           # fluxo de branches, commits e PR
├── CHANGELOG.md              # histórico de versões da documentação
└── README.md
```

### 1.3 Infraestrutura local

O `docker-compose.yml` sobe quatro serviços: PostgreSQL 17, Redis 7, MinIO e Mailpit. Mailpit captura e-mails em vez de enviá-los, o que evita disparar mensagem real em desenvolvimento. A major version do banco local é a mesma de staging e produção (**PostgreSQL 17**); a divergência entre ambientes é proibida pelo [ADR-008](adr/ADR-008-supabase-postgresql-gerenciado.md).

```yaml
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: sosp
      POSTGRES_USER: sosp
      POSTGRES_PASSWORD: sosp
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sosp -d sosp"]
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data

  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "1025:1025"
      - "8025:8025"

volumes:
  pgdata:
  redisdata:
  miniodata:
```

```bash
docker compose up -d
docker compose ps
```

**Critério de sucesso:** `docker compose ps` mostra `postgres` e `redis` como `healthy`, e as portas 9000, 9001 e 8025 respondem.

**Por que não há Supabase local.** O Supabase é usado somente como PostgreSQL gerenciado em staging e produção ([ADR-008](adr/ADR-008-supabase-postgresql-gerenciado.md)). Em desenvolvimento, o banco é o contêiner local, com o mesmo schema e a mesma major version. Ninguém precisa de conta no Supabase para rodar o projeto; o `.env` local nunca aponta para o banco de produção.

### 1.4 Back-end

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

```bash
cp ../.env.example ../.env
```

O arquivo `.env` fica na raiz do repositório e é lido pelo Django e pelo Next.js. Ele **nunca** é comitado. O `.env.example` canônico também está na raiz; não existe cópia em `docs/`.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata ../fixtures/genders.json
python manage.py loaddata ../fixtures/notification_templates.json
python manage.py loaddata ../fixtures/search_synonyms.json
python manage.py loaddata ../fixtures/demo_catalog.json
```

```bash
python manage.py runserver 0.0.0.0:8000
```

Em outro terminal, os workers:

```bash
cd backend
source .venv/bin/activate
celery -A config worker -l info -Q pdf,email,reminders,reports,maintenance
```

```bash
cd backend
source .venv/bin/activate
celery -A config beat -l info
```

**Fila `push`.** O MVP envia apenas e-mail transacional. A fila `push` e o worker correspondente só entram em operação na v2.0, com `FEATURE_PUSH_ENABLED=true` ([ADR-007](adr/ADR-007-feature-flags.md)); por isso ela não aparece no comando acima.

**Critério de sucesso:** `curl http://localhost:8000/api/v1/services` retorna `200` com a lista paginada, e `http://localhost:8000/admin` abre a tela de login.

### 1.5 Front-end

```bash
cd portal
npm install
npm run dev
```

**Critério de sucesso:** `http://localhost:3000` abre a home, a busca retorna serviços do fixture e a ficha renderiza os oito blocos.

### 1.6 Massa de demonstração

O fixture `demo_catalog.json` cria um recorte mínimo e coerente:

| Entidade | Quantidade | Conteúdo |
|---|---|---|
| Órgãos | 3 | DETRAN (estadual), SEMED (municipal), INSS (federal) |
| Unidades | 4 | Duas em Maceió, uma em Arapiraca, uma em Recife |
| Serviços | 8 | Documentos, saúde, educação, transporte e assistência social |
| Etapas | 24 | Três etapas por serviço, em média |
| Documentos | 16 | Dois por serviço, ao menos um obrigatório |
| FAQ | 12 | Perguntas vinculadas a serviços e a categorias |
| Sinônimos | 7 | `rg`, `cpf`, `sus`, `inss`, `detran`, `crás`, `certidão` |
| Templates | 5 | Conta criada, agendamento, lembrete, status e dúvida respondida |

**Regra de privacidade:** nenhum fixture usa CPF, e-mail ou telefone de pessoa real. Os CPFs são válidos apenas pelo dígito verificador e reservados para teste (RS-01, RNF-12).

### 1.7 Comandos de teste

```bash
cd backend
source .venv/bin/activate
pytest
pytest --cov=apps --cov-report=term-missing --cov-fail-under=80
```

```bash
cd portal
npm run lint
npm run test
npm run test:coverage
npx playwright test
```

```bash
# contrato OpenAPI
python -c "from openapi_spec_validator import validate; from openapi_spec_validator.readers import read_from_filename; validate(read_from_filename('../docs/api/openapi.yaml')[0])"
```

### 1.8 Acessos de desenvolvimento

| Serviço | URL | Credencial |
|---|---|---|
| Portal | `http://localhost:3000` | Cidadão via CPF + senha (Gov.br como v2.0) |
| API | `http://localhost:8000/api/v1` | — |
| Django Admin | `http://localhost:8000/admin` | Superusuário criado no passo 1.4 |
| Mailpit | `http://localhost:8025` | Sem autenticação |
| MinIO Console | `http://localhost:9001` | `minioadmin` / `minioadmin` |
| PostgreSQL | `localhost:5432` | `sosp` / `sosp` |
| Redis | `localhost:6379` | Sem senha em desenvolvimento |

**Autenticação local:** cidadãos e servidores autenticam com CPF + senha. O botão "Entrar com Gov.br" exibe modal de implementação futura (v2.0) e não requer credenciais de homologação no MVP. Em staging, o envio de e-mail usa Mailpit ou provedor transacional configurado.

### 1.9 Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `connection refused` em 5432 | Postgres não subiu | `docker compose up -d postgres` e conferir `docker compose logs postgres` |
| `password authentication failed` | `.env` com URL divergente do compose | Conferir `DATABASE_URL`; o compose usa `sosp:sosp` |
| `relation "..." does not exist` | Migrações não aplicadas | `python manage.py migrate` |
| `django.db.utils.OperationalError` no teste | Banco de teste sem permissão | `pytest --create-db`; o usuário precisa de `CREATEDB` |
| PDF nunca fica pronto | Worker não está rodando | Subir o worker com a fila `pdf` |
| E-mail não chega | Mailpit não está aberto | Abrir `http://localhost:8025`; o SMTP é `localhost:1025` |
| `next: command not found` | `npm install` não rodou | `cd portal && npm install` |
| CORS ou cookie não persiste | Origem diferente de `localhost:3000` | Ajustar `DJANGO_CSRF_TRUSTED_ORIGINS` e acessar pela URL correta |
| Upload rejeitado | ClamAV não está rodando | Subir o serviço ou definir `CLAMAV_ENABLED=false` em desenvolvimento |
| `too many connections` em staging | Pooler do Supabase esgotado ou workers demais | Reduzir concorrência, conferir `DATABASE_CONN_MAX_AGE` e monitorar conexões antes da demo |
| `prepared statement ... already exists` | Uso do Transaction pooler (porta 6543) com Django | Usar o Session pooler (porta 5432) ou definir `DATABASE_DISABLE_SERVER_SIDE_CURSORS=true` e `DATABASE_CONN_MAX_AGE=0` |
| `server-side cursors` ou cursor perdido | Pooler em modo transação | Trocar para o Session pooler; ver [ADR-008](adr/ADR-008-supabase-postgresql-gerenciado.md) |

---

## 2. Configuração e segredos

### 2.1 Arquivo `.env.example`

O arquivo canônico é [`/.env.example`](../.env.example), na raiz do repositório. Ele documenta cada chave com valor de exemplo e comentário, agrupada por área: Django, banco, Redis/Celery, Gov.br, endereço, e-mail, push, storage, observabilidade, portal, sessão, upload, feature flags e build. O `.env` real é copiado a partir dele e nunca entra no Git.

```bash
cp .env.example .env
```

**Regra:** não existe `.env.example` dentro de `docs/`. A cópia antiga foi removida para não criar duas fontes de verdade; qualquer referência a `docs/.env.example` está errada. O CI usa o arquivo da raiz para validar flags e para extrair `APP_VERSION` na tag de release.

### 2.2 Variáveis

| Variável | Exemplo | Obrigatória | Secreta | Descrição |
|---|---|---|---|---|
| `DJANGO_SECRET_KEY` | `dev-only-change-me` | Sim | Sim | Chave de assinatura de sessão e CSRF |
| `DJANGO_DEBUG` | `true` | Sim | Não | `false` em staging e produção |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Sim | Não | Hosts aceitos pelo Django |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:3000` | Sim | Não | Origens confiáveis para CSRF |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` | Sim | Não | Módulo de settings por ambiente |
| `DJANGO_SECURE_SSL_REDIRECT` | `false` | Sim | Não | Redireciona HTTP para HTTPS |
| `DATABASE_URL` | `postgres://sosp:sosp@localhost:5432/sosp` | Sim | Sim | Conexão da aplicação; local no Docker, staging/produção no **Session pooler** do Supabase (`sslmode=require`) |
| `DATABASE_DIRECT_URL` | `postgres://sosp:sosp@localhost:5432/sosp` | Sim | Sim | Conexão **direta** para migrações, `pg_dump` e scripts; nunca usada pela API em runtime |
| `DATABASE_CONN_MAX_AGE` | `60` | Não | Não | Reuso de conexão em segundos; `0` no Transaction pooler |
| `DATABASE_STATEMENT_TIMEOUT_MS` | `5000` | Não | Não | Limite de execução por query |
| `DATABASE_DISABLE_SERVER_SIDE_CURSORS` | `false` | Não | Não | `true` apenas no Transaction pooler (porta 6543); `false` no Session pooler |
| `REDIS_URL` | `redis://localhost:6379/0` | Sim | Sim | Cache e sessão |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Sim | Sim | Broker das filas |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Sim | Sim | Resultados de tarefas |
| `CELERY_TASK_ALWAYS_EAGER` | `false` | Não | Não | Executa tarefas inline em teste |
| `GOVBR_CLIENT_ID` | `sosp-homolog` | Sim | Não | Client ID OIDC |
| `GOVBR_CLIENT_SECRET` | `change-me` | Sim | Sim | Client secret OIDC |
| `GOVBR_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/govbr/callback` | Sim | Não | URL de callback registrada |
| `GOVBR_AUTHORIZE_URL` | `https://sso.staging.acesso.gov.br/authorize` | Sim | Não | Endpoint de autorização |
| `GOVBR_TOKEN_URL` | `https://sso.staging.acesso.gov.br/token` | Sim | Não | Endpoint de token |
| `GOVBR_JWKS_URL` | `https://sso.staging.acesso.gov.br/jwk` | Sim | Não | Chaves públicas para validar `id_token` |
| `GOVBR_SCOPE` | `openid profile email govbr_confiabilidades` | Sim | Não | Escopos solicitados |
| `FEATURE_GOVBR_INTEGRATION_ENABLED` | `false` | Sim | Não | Liga o fluxo OIDC real do Gov.br (v2.0) |
| `VIACEP_BASE_URL` | `https://viacep.com.br/ws` | Sim | Não | Base da consulta de CEP |
| `IBGE_BASE_URL` | `https://servicodados.ibge.gov.br/api/v1/localidades` | Sim | Não | Base de municípios e UF |
| `EMAIL_HOST` | `localhost` | Sim | Não | Servidor SMTP |
| `EMAIL_PORT` | `1025` | Sim | Não | Porta SMTP |
| `EMAIL_HOST_USER` | vazio | Não | Sim | Usuário SMTP |
| `EMAIL_HOST_PASSWORD` | vazio | Não | Sim | Senha SMTP |
| `EMAIL_USE_TLS` | `false` | Sim | Não | TLS no SMTP |
| `DEFAULT_FROM_EMAIL` | `nao-responda@sosp.gov.br` | Sim | Não | Remetente padrão |
| `EMAIL_WEBHOOK_SECRET` | `dev-only-webhook-secret` | Sim | Sim | Segredo HMAC dos eventos do provedor de e-mail |
| `EMAIL_WEBHOOK_TOLERANCE_SECONDS` | `300` | Sim | Não | Janela anti-replay do webhook, em segundos |
| `WEBPUSH_PUBLIC_KEY` | `dev-public-key-replace-me` | Não (v2.0) | Não | Chave pública VAPID; só necessária com `FEATURE_PUSH_ENABLED=true` |
| `WEBPUSH_PRIVATE_KEY` | `dev-private-key-replace-me` | Não (v2.0) | Sim | Chave privada VAPID; só necessária com `FEATURE_PUSH_ENABLED=true` |
| `WEBPUSH_SUBJECT` | `mailto:equipe.sosp@cesmac.edu.br` | Não (v2.0) | Não | Contato VAPID |
| `AWS_ACCESS_KEY_ID` | `minioadmin` | Sim | Sim | Chave de acesso ao storage |
| `AWS_SECRET_ACCESS_KEY` | `minioadmin` | Sim | Sim | Segredo do storage |
| `AWS_STORAGE_BUCKET_NAME` | `sosp-local` | Sim | Não | Bucket de anexos e PDFs |
| `AWS_S3_ENDPOINT_URL` | `http://localhost:9000` | Sim | Não | Endpoint S3/MinIO |
| `AWS_S3_REGION_NAME` | `us-east-1` | Sim | Não | Região do bucket |
| `AWS_S3_USE_SSL` | `false` | Sim | Não | TLS no storage |
| `AWS_S3_ADDRESSING_STYLE` | `path` | Sim | Não | Estilo de endereçamento do MinIO |
| `MINIO_ROOT_USER` | `minioadmin` | Sim | Sim | Usuário do MinIO local |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | Sim | Sim | Senha do MinIO local |
| `SIGNED_URL_TTL_SECONDS` | `300` | Sim | Não | Expiração de URL assinada |
| `SENTRY_DSN` | vazio | Não | Sim | DSN do Sentry |
| `SENTRY_ENVIRONMENT` | `development` | Sim | Não | Ambiente no Sentry |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Não | Não | Amostragem de traces |
| `PROMETHEUS_METRICS_ENABLED` | `true` | Não | Não | Expõe `/metrics` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | vazio | Não | Não | Coletor OpenTelemetry |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | Sim | Não | Base da API no portal |
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3000` | Sim | Não | URL pública do portal |
| `NEXT_PUBLIC_WEBPUSH_PUBLIC_KEY` | `dev-public-key-replace-me` | Não (v2.0) | Não | Chave pública exposta ao navegador; só necessária com push ligado |
| `NEXT_TELEMETRY_DISABLED` | `1` | Não | Não | Desliga telemetria do Next.js |
| `SESSION_COOKIE_AGE` | `1800` | Sim | Não | Duração da sessão em segundos |
| `SESSION_IDLE_TIMEOUT_SECONDS` | `1800` | Sim | Não | Inatividade máxima |
| `LOGIN_MAX_ATTEMPTS` | `5` | Sim | Não | Tentativas antes do bloqueio |
| `LOGIN_LOCKOUT_MINUTES` | `5` | Sim | Não | Duração do bloqueio |
| `RATE_LIMIT_ENABLED` | `true` | Sim | Não | Liga o rate limit |
| `CLAMAV_HOST` | `localhost` | Sim | Não | Host do antivírus |
| `CLAMAV_PORT` | `3310` | Sim | Não | Porta do antivírus |
| `CLAMAV_ENABLED` | `true` | Sim | Não | Desliga apenas em desenvolvimento |
| `MAX_UPLOAD_SIZE_MB` | `10` | Sim | Não | Limite de anexo |
| `FEATURE_REVIEWS_ENABLED` | `false` | Sim | Não | Liga o RF-10 (avaliação, v2.0) |
| `FEATURE_NOTIFICATION_CENTER_ENABLED` | `false` | Sim | Não | Liga a central de preferências do RF-13 (v2.0) |
| `FEATURE_PUSH_ENABLED` | `false` | Sim | Não | Liga o Web Push do RF-13 (v2.0); o MVP usa só e-mail |
| `FEATURE_SMS_ENABLED` | `false` | Sim | Não | Liga SMS da Fase 3 |
| `FEATURE_WHATSAPP_ENABLED` | `false` | Sim | Não | Liga WhatsApp da Fase 3 |
| `FEATURE_REPORTS_EXPORT` | `true` | Sim | Não | Liga a exportação CSV/PDF do RF-14; já entregue no MVP |
| `APP_VERSION` | `1.0.0` | Sim | Não | Versão exibida no healthcheck |
| `GIT_SHA` | `local` | Sim | Não | Commit do build |

### 2.3 Gestão por ambiente

| Ambiente | Origem dos segredos | Quem lê | Rotação |
|---|---|---|---|
| Desenvolvimento | `.env` local, cópia do `.env.example` da raiz | Desenvolvedor | Nunca usa segredo real |
| Staging | Secret manager do provedor + variáveis do pipeline | Pipeline e aplicação | A cada 90 dias |
| Produção | Secret manager com acesso auditado | Apenas a aplicação e o plantão | A cada 90 dias ou em incidente |

**Regras**

1. Segredo nunca entra na imagem Docker, no repositório ou no log.
2. O pipeline injeta segredos em tempo de execução, não de build.
3. Chaves de Gov.br, SMTP, VAPID e S3 têm donos nomeados e prazo de validade. VAPID só é exigida com push ligado.
4. `DJANGO_SECRET_KEY` de produção é diferente de staging; trocar a chave invalida sessões, o que é aceitável em rotação planejada.
5. A aplicação falha no boot se uma variável obrigatória estiver ausente (`django.core.checks`).
6. **Supabase:** `DATABASE_URL` (Session pooler) e `DATABASE_DIRECT_URL` (conexão direta) ficam no secret manager do ambiente. O acesso ao painel do Supabase é restrito à equipe; a `service_role` não é configurada em nenhum ambiente da aplicação, nem no portal, nem no repositório ([ADR-008](adr/ADR-008-supabase-postgresql-gerenciado.md)).
7. **Uma porta de escrita:** nenhuma variável `NEXT_PUBLIC_*` contém credencial de banco ou chave administrativa do Supabase. O portal só conhece `NEXT_PUBLIC_API_BASE_URL`.

### 2.4 Rotação de segredos

| Segredo | Procedimento | Impacto | Rollback |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Nova chave + janela de convivência de 24 h | Sessões antigas expiram | Restaurar chave anterior |
| `GOVBR_CLIENT_SECRET` | Trocar no provedor e no secret manager | Login do cidadão falha se divergir | Reverter no provedor |
| SMTP | Nova credencial no provedor e no secret manager | E-mails falham até propagar | Reverter credencial |
| VAPID | Novo par de chaves e reassinatura no navegador | Push exige nova inscrição | Manter par antigo por 30 dias |
| S3/MinIO | Nova chave IAM com menor privilégio | Anexos e PDFs falham | Reverter política |
| HMAC do webhook | Segredo rotativo com dois valores ativos | Eventos rejeitados se divergir | Usar segredo anterior |

### 2.5 Validação no boot

```python
# config/checks.py
from django.core.checks import Error, register
from django.conf import settings


@register()
def required_settings_check(app_configs, **kwargs):
    errors = []
    required = [
        "DATABASE_URL",
        "REDIS_URL",
        "GOVBR_CLIENT_ID",
        "GOVBR_CLIENT_SECRET",
        "GOVBR_REDIRECT_URI",
        "DEFAULT_FROM_EMAIL",
    ]
    for name in required:
        if not getattr(settings, name, None):
            errors.append(
                Error(
                    f"{name} não configurada.",
                    hint="Copie .env.example para .env e preencha o valor.",
                    id="sosp.E001",
                )
            )
    return errors
```

**Critério de sucesso:** subir a API sem `DATABASE_URL` falha imediatamente com `sosp.E001`, em vez de quebrar na primeira requisição.

---

## 3. Padrões de código e Git

### 3.1 Git Flow simplificado

O repositório adota **Git Flow simplificado**: `main` (produção) + `develop` (integração). A decisão completa está no [ADR-004](adr/ADR-004-git-flow-simplificado.md) e o resumo prático no [CONTRIBUTING](../CONTRIBUTING.md). Este fluxo substitui a decisão implícita anterior de Trunk-Based Development.

| Branch | Origem | Destino | Uso |
|---|---|---|---|
| `main` | — | — | Produção; sempre estável; só recebe merge de `release/*` e `hotfix/*` |
| `develop` | `main` | — | Integração; deploy automático em staging |
| `feat/<área>/<id>-<descrição>` | `develop` | `develop` | Nova funcionalidade |
| `fix/<área>/<id>-<descrição>` | `develop` | `develop` | Correção não urgente |
| `docs/`, `chore/`, `test/`, `refactor/` | `develop` | `develop` | Demais tipos |
| `release/vX.Y.Z` | `develop` | `main` e `develop` | Estabilização da versão |
| `hotfix/<descrição>` | `main` | `main` e `develop` | Correção urgente em produção |

**Proibido:** commit direto e force push em `main` e `develop`; merge sem revisão e sem CI verde.

**Separação por área**

| Área | Caminho | Exemplo de branch | Exemplo de commit |
|---|---|---|---|
| `back` | `backend/` | `feat/back/rf06-endpoint-busca` | `feat(back/search): adiciona filtro por município` |
| `front` | `portal/` | `feat/front/rf06-tela-busca` | `feat(front/search): implementa filtro por município` |
| `full` | ambos | `feat/full/rf08-campo-observacao` | `feat(full/scheduling): adiciona observação` |

Etiquetas no GitHub: `area:backend`, `area:frontend`, `area:fullstack`, além de etiquetas por requisito (`RF-06`, `RF-08`…). O campo **Área** do GitHub Projects permite filtrar o quadro por time.

**Tarefas que envolvem front e back (contract-first)**

1. Toda tarefa fullstack nasce como **issue principal** (`area:fullstack`) com três sub-issues: **contrato**, **back** e **front**.
2. O primeiro PR (`feat/back/<id>-contrato`) altera **apenas** `docs/api/openapi.yaml` e é revisado por um dev de cada área.
3. Após o merge do contrato em `develop`, back e front trabalham em paralelo em branches próprias. O front usa mock gerado do OpenAPI (Prism/MSW) até a API estar disponível.
4. A issue principal só fecha quando as três sub-issues estiverem concluídas.
5. **Exceção:** mudanças pequenas (≤ 1–2 dias e ≤ ~400 linhas somando os dois lados) podem usar uma única branch `feat/full/...`, exigindo um revisor de cada área.

```mermaid
flowchart LR
    A[Issue principal area:fullstack] --> B[Sub-issue contrato]
    B --> C[PR feat/back/id-contrato<br/>apenas openapi.yaml]
    C --> D[Merge em develop]
    D --> E[Back em paralelo]
    D --> F[Front em paralelo<br/>mock Prism/MSW]
    E --> G[PR back]
    F --> H[PR front]
    G --> I[Merge em develop]
    H --> I
    I --> J[release/vX.Y.Z]
    J --> K[Merge em main + tag]
    K --> L[Deploy produção]
    I --> M[Deploy staging]
```

### 3.2 Conventional Commits

Formato: `<tipo>(<escopo>): <descrição no imperativo>`.

| Tipo | Uso | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat(search): adiciona filtro por município` |
| `fix` | Correção de defeito | `fix(scheduling): impede overbooking no último slot` |
| `docs` | Documentação | `docs(adr): registra convenção camelCase` |
| `test` | Teste | `test(search): cobre busca sem acento` |
| `refactor` | Refatoração sem mudança de comportamento | `refactor(catalog): extrai selector de unidade` |
| `perf` | Melhoria de desempenho | `perf(search): adiciona índice GIN` |
| `build` | Build e dependências | `build(deps): atualiza Django para 5.2` |
| `ci` | Pipeline | `ci: adiciona validação do OpenAPI` |
| `chore` | Manutenção | `chore: atualiza .gitignore` |
| `revert` | Reversão | `revert: remove filtro instável` |

**Regras:** assunto com até 72 caracteres, sem ponto final, corpo opcional explicando o "porquê", rodapé com `Refs: RF-06` ou `Closes: #123`.

### 3.3 Checklist de Pull Request

| # | Item | Evidência |
|---|---|---|
| 1 | Área identificada (back/front/full) | Nome da branch e etiqueta GitHub |
| 2 | Branch de destino correta (`develop`, ou `main` apenas para release/hotfix) | Nome da branch e campo de base |
| 3 | O PR referencia o RF, RNF ou RS | Descrição com `Refs:` |
| 4 | Testes novos cobrem o comportamento | Diff de testes |
| 5 | CI verde | Checks do GitHub |
| 6 | Cobertura não caiu | Relatório do CI |
| 7 | Nenhum módulo importa model de outro | `check_module_boundaries.py` |
| 8 | Nenhum identificador com maiúscula no banco | `check_identifiers.py` |
| 9 | Contrato OpenAPI atualizado quando a rota muda | `openapi.yaml` no diff |
| 10 | Migração tem `forward` e `reverse` | Arquivo de migração |
| 11 | Acessibilidade verificada em tela alterada | axe-core + teclado |
| 12 | Nenhum dado pessoal em log ou fixture | Revisão |
| 13 | Feature flag documentada, se aplicável | `.env.example` + Pilar 5 §10 |
| 14 | Texto de UI em PT-BR e identificador em EN | Revisão |

### 3.4 Lint e formatação

```toml
# backend/pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "DJ", "S", "C4", "SIM"]
ignore = ["S101"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"
markers = [
  "unit: teste unitário sem banco",
  "integration: teste com banco e API",
  "e2e: teste Playwright",
  "slow: teste de carga ou longa duração",
]

[tool.coverage.run]
source = ["apps"]
omit = ["*/migrations/*", "*/tests/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

```js
// portal/eslint.config.mjs
import js from "@eslint/js";
import next from "@next/eslint-plugin-next";
import tseslint from "typescript-eslint";

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: { "@next/next": next },
    rules: {
      ...next.configs.recommended.rules,
      "@next/next/no-html-link-for-pages": "off",
      "no-console": ["error", { allow: ["warn", "error"] }],
    },
  },
];
```

```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100
}
```

**Comandos:**

```bash
cd backend
ruff check .
ruff format --check .
black --check .
```

```bash
cd portal
npm run lint
npx prettier --check .
```

### 3.5 Revisão de código

| Regra | Valor |
|---|---|
| Revisores obrigatórios | 1 para mudança comum; 2 para migração, segurança ou contrato |
| Tamanho ideal do PR | Até 400 linhas alteradas |
| Prazo de primeira resposta | 1 dia útil |
| Autor resolve comentário | Sim; revisor confirma |
| Merge | Apenas com CI verde e conversas resolvidas |
| Revisão de segurança | Obrigatória em `accounts`, `audit`, upload e autorização |

---

## 4. Estratégia de testes

### 4.1 Pirâmide

| Nível | Ferramenta | O que cobre | Tempo alvo | Proporção |
|---|---|---|---|---|
| Unitário | pytest + factory_boy | Regra de serviço, cálculo de slot, protocolo, validação | < 5 s por arquivo | 60% |
| Integração | pytest-django + DRF APIClient | API + banco + permissão + transação | < 60 s | 30% |
| Contrato | openapi-spec-validator + schemathesis | Aderência ao `openapi.yaml` | < 30 s | 5% |
| E2E | Playwright | Busca → ficha → guia → agendamento → protocolo | < 10 min | 5% |
| Carga | k6 | p95/p99 com 1.000 usuários simultâneos | Execução noturna | Pontual |
| Segurança | bandit, pip-audit, OWASP ZAP | Dependência, injeção, headers | Semanal | Pontual |
| Visual | Playwright screenshot | Regressão de componentes e telas críticas | < 5 min | Pontual |

**Regra:** um teste E2E não substitui um teste de serviço. Se a regra só é testada no navegador, o defeito é encontrado tarde e diagnosticado mal.

### 4.2 Teste unitário de serviço

```python
# backend/apps/scheduling/tests/test_services.py
from datetime import date, time, timedelta

import pytest
from django.utils import timezone

from apps.scheduling.services import (
    DuplicateAppointmentError,
    SlotUnavailableError,
    create_appointment,
)
from apps.scheduling.tests.factories import (
    AppointmentFactory,
    CitizenFactory,
    ServiceFactory,
    SlotFactory,
    UnitFactory,
)


@pytest.mark.unit
@pytest.mark.django_db
class TestCreateAppointment:
    def test_cria_agendamento_e_protocolo(self):
        citizen = CitizenFactory()
        service = ServiceFactory()
        unit = UnitFactory()
        target = timezone.localdate() + timedelta(days=1)
        SlotFactory(unit=unit, slot_date=target, starts_at=time(9, 0), capacity=1)

        appointment = create_appointment(
            citizen_id=citizen.id,
            service_id=service.id,
            unit_id=unit.id,
            scheduled_date=target,
            scheduled_time=time(9, 0),
        )

        assert appointment.status == "scheduled"
        assert appointment.protocol_number == appointment.protocol.protocol_number
        assert appointment.protocol.status == "received"

    def test_bloqueia_data_passada(self):
        citizen = CitizenFactory()
        service = ServiceFactory()
        unit = UnitFactory()

        with pytest.raises(ValueError, match="data passada"):
            create_appointment(
                citizen_id=citizen.id,
                service_id=service.id,
                unit_id=unit.id,
                scheduled_date=date.today() - timedelta(days=1),
                scheduled_time=time(9, 0),
            )

    def test_bloqueia_duplicidade_ativa(self):
        appointment = AppointmentFactory(status="scheduled")

        with pytest.raises(DuplicateAppointmentError):
            create_appointment(
                citizen_id=appointment.citizen_id,
                service_id=appointment.service_id,
                unit_id=appointment.unit_id,
                scheduled_date=appointment.scheduled_date,
                scheduled_time=appointment.scheduled_time,
            )

    def test_bloqueia_slot_lotado(self):
        citizen = CitizenFactory()
        service = ServiceFactory()
        unit = UnitFactory()
        target = timezone.localdate() + timedelta(days=1)
        SlotFactory(
            unit=unit,
            slot_date=target,
            starts_at=time(10, 0),
            capacity=1,
            booked_count=1,
        )

        with pytest.raises(SlotUnavailableError):
            create_appointment(
                citizen_id=citizen.id,
                service_id=service.id,
                unit_id=unit.id,
                scheduled_date=target,
                scheduled_time=time(10, 0),
            )
```

### 4.3 Teste de integração de API

```python
# backend/apps/search/tests/test_api.py
import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import ServiceFactory


@pytest.mark.integration
@pytest.mark.django_db
class TestSearchApi:
    def test_busca_sem_acento(self):
        ServiceFactory(name="Certidão de Nascimento", status="active")
        client = APIClient()

        response = client.get("/api/v1/services", {"q": "certidao"})

        assert response.status_code == 200
        assert response.json()["pagination"]["total"] == 1

    def test_busca_vazia_lista_ativos(self):
        ServiceFactory.create_batch(3, status="active")
        ServiceFactory(status="draft")
        client = APIClient()

        response = client.get("/api/v1/services", {"q": ""})

        assert response.status_code == 200
        assert response.json()["pagination"]["total"] == 3

    def test_page_size_acima_do_limite_retorna_400(self):
        client = APIClient()

        response = client.get("/api/v1/services", {"pageSize": 51})

        assert response.status_code == 400
        assert response.json()["status"] == 400

    def test_protocolo_de_terceiro_retorna_404(self):
        client = APIClient()
        client.force_authenticate(user=None)

        response = client.get("/api/v1/protocols/20261112-9999")

        assert response.status_code == 404
```

### 4.4 Teste de contrato

```bash
python -c "
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename
spec, _ = read_from_filename('docs/api/openapi.yaml')
validate(spec)
print('OpenAPI válido')
"
```

```python
# backend/tests/test_openapi_contract.py
import pytest
import schemathesis

schema = schemathesis.from_path("../docs/api/openapi.yaml", base_url="http://localhost:8000")


@pytest.mark.integration
@schema.parametrize()
def test_api_aderente_ao_contrato(case):
    response = case.call()
    case.validate_response(response)
```

**Regra:** o contrato é validado em todo PR. Rota nova sem schema quebra o build.

### 4.5 E2E com Playwright

```ts
// portal/e2e/journey.spec.ts
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("busca, ficha e agendamento", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("searchbox", { name: /buscar serviço/i }).fill("tirar rg");
  await page.getByRole("button", { name: /buscar/i }).click();

  await expect(page.getByRole("heading", { name: /resultados/i })).toBeVisible();
  await page.getByRole("link", { name: /emitir carteira de identidade/i }).click();

  await expect(page.getByRole("heading", { name: /o que é/i })).toBeVisible();
  await expect(page.getByText(/gratuito/i)).toBeVisible();

  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);

  await page.getByRole("link", { name: /agendar/i }).click();
  await expect(page.getByText(/entre para agendar/i)).toBeVisible();
});

test("estado vazio usa a mensagem literal", async ({ page }) => {
  await page.goto("/busca?q=passaporte%20intergalactico");

  await expect(
    page.getByText("Nenhum serviço encontrado. Tente outro termo ou categoria."),
  ).toBeVisible();
});
```

```ts
// portal/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit-mobile", use: { ...devices["iPhone 13"] } },
  ],
  webServer: {
    command: "npm run start",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

### 4.6 Regressão visual

| Alvo | Quantidade | Ferramenta | Critério |
|---|---|---|---|
| Componentes do Design System | 40 | Playwright screenshot | Diferença máxima de 0,1% por pixel |
| Telas críticas | 6 | Playwright screenshot | Busca, ficha, guia, agendamento, protocolo, login |
| Larguras | 390 px, 768 px, 1200 px | Projetos do Playwright | Nenhuma quebra de layout |

**Regra:** atualização de snapshot exige revisão de design no PR. Snapshot atualizado sem justificativa é regressão silenciosa.

### 4.7 Teste de carga

```js
// scripts/k6/search.js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    search: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "2m", target: 1000 },
        { duration: "5m", target: 1000 },
        { duration: "1m", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<2500", "p(99)<3000"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const response = http.get(
    `${__ENV.BASE_URL}/api/v1/services?q=certidao&page=1&pageSize=10`,
  );

  check(response, {
    "status 200": (r) => r.status === 200,
    "tem itens": (r) => JSON.parse(r.body).items.length > 0,
  });

  sleep(1);
}
```

```bash
k6 run -e BASE_URL=https://staging.sosp.gov.br scripts/k6/search.js
```

**Critério:** p95 ≤ 2,5 s e p99 ≤ 3,0 s com 1.000 usuários simultâneos (RNF-04). PDF: p95 ≤ 4 s e p99 ≤ 5 s com 20 jobs por minuto.

### 4.8 Testes de segurança

| Teste | Ferramenta | O que verifica | Frequência |
|---|---|---|---|
| Dependências vulneráveis | `pip-audit` e `npm audit` | CVE conhecida | Todo PR |
| Análise estática | `bandit` | Injeção, `eval`, segredo hardcoded | Todo PR |
| Headers | OWASP ZAP baseline | HSTS, CSP, `X-Content-Type-Options` | Semanal |
| Autorização | pytest por papel | 403 e 404 corretos por rota | Todo PR |
| Upload | pytest com arquivo malicioso | Extensão, MIME real, tamanho, antivírus | Todo PR |
| Força bruta | pytest com relógio controlado | Bloqueio após 5 tentativas | Todo PR |
| Sessão | pytest | Expiração em 30 min e revogação | Todo PR |

### 4.9 Cobertura e qualidade

| Métrica | Limite | Bloqueia merge | Onde |
|---|---|---|---|
| Cobertura back-end | ≥ 80% | Sim | `pytest --cov-fail-under=80` |
| Cobertura portal | ≥ 70% | Sim | `npm run test:coverage` |
| Complexidade ciclomática | ≤ 10 por função | Sim | `ruff` e revisão |
| Duplicação | ≤ 3% | Não | Relatório semanal |
| Vulnerabilidade crítica | 0 | Sim | `pip-audit` e `npm audit` |
| Violação axe crítica | 0 | Sim | Playwright + axe |

### 4.10 Dados de teste e LGPD

1. Fixture não usa CPF, e-mail, telefone ou endereço de pessoa real.
2. CPF de teste é sintético e válido pelo dígito verificador, marcado no nome do fixture.
3. Dump de produção só entra em staging após anonimização de CPF, e-mail, telefone, endereço, PCD e nome.
4. Teste de login usa mock local; no MVP o login é local (CPF + senha), sem dependência de provedor externo.
5. Log de teste não imprime dado pessoal; o filtro de PII é testado.

---

## 5. CI/CD

### 5.1 Pipeline

```mermaid
flowchart LR
    A[Push ou PR] --> B[Lint]
    B --> C[Test]
    C --> D[Contract]
    D --> E[Build]
    E --> F[Migrate staging]
    F --> G[Deploy staging]
    G --> H[Smoke]
    H --> I{Aprovado?}
    I -->|Sim| J[Deploy produção]
    I -->|Nao| K[Bloqueia e notifica]
    J --> L[Smoke produção]
    L --> M[Monitoração 30 min]
```

**Regra:** um pipeline único por deployável (Django e Next.js), com jobs independentes. O portal não espera a API para buildar, mas o deploy de produção espera os dois smoke tests.

### 5.2 Workflow de referência

```yaml
name: ci

on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop, main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "22"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -e "./backend[dev]"
      - run: ruff check backend
      - run: black --check backend
      - run: python backend/scripts/check_module_boundaries.py
      - run: python backend/scripts/check_identifiers.py
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
          cache-dependency-path: portal/package-lock.json
      - run: npm ci
        working-directory: portal
      - run: npm run lint
        working-directory: portal
      - run: npx prettier --check .
        working-directory: portal

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_DB: sosp_test
          POSTGRES_USER: sosp
          POSTGRES_PASSWORD: sosp
        ports:
          - "5432:5432"
        options: >-
          --health-cmd "pg_isready -U sosp -d sosp_test"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10
    env:
      DATABASE_URL: postgres://sosp:sosp@localhost:5432/sosp_test
      REDIS_URL: redis://localhost:6379/0
      DJANGO_SETTINGS_MODULE: config.settings.test
      DJANGO_SECRET_KEY: ci-only-not-a-secret
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -e "./backend[dev]"
      - run: python backend/manage.py migrate --noinput
      - run: pytest backend --cov=backend/apps --cov-report=xml --cov-fail-under=80
      - run: python -c "from openapi_spec_validator import validate; from openapi_spec_validator.readers import read_from_filename; validate(read_from_filename('docs/api/openapi.yaml')[0])"
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage
          path: coverage.xml

  e2e:
    runs-on: ubuntu-latest
    needs: test
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_DB: sosp_test
          POSTGRES_USER: sosp
          POSTGRES_PASSWORD: sosp
        ports:
          - "5432:5432"
        options: >-
          --health-cmd "pg_isready -U sosp -d sosp_test"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10
    env:
      DATABASE_URL: postgres://sosp:sosp@localhost:5432/sosp_test
      REDIS_URL: redis://localhost:6379/0
      DJANGO_SETTINGS_MODULE: config.settings.test
      DJANGO_SECRET_KEY: ci-only-not-a-secret
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000/api/v1
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
          cache-dependency-path: portal/package-lock.json
      - run: pip install -e "./backend[dev]"
      - run: python backend/manage.py migrate --noinput
      - run: python backend/manage.py loaddata fixtures/demo_catalog.json
      - run: npm ci
        working-directory: portal
      - run: npx playwright install --with-deps
        working-directory: portal
      - run: npx playwright test
        working-directory: portal
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: portal/playwright-report

  build:
    runs-on: ubuntu-latest
    needs: [test, e2e]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: backend
          push: true
          tags: ghcr.io/${{ github.repository }}/api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      - uses: docker/build-push-action@v6
        with:
          context: portal
          push: true
          tags: ghcr.io/${{ github.repository }}/portal:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy.sh staging "${{ github.sha }}"
      - run: ./scripts/smoke.sh https://staging.sosp.gov.br

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy.sh production "${{ github.sha }}"
      - run: ./scripts/smoke.sh https://sosp.gov.br
```

### 5.3 Contrato dos scripts de deploy

O pipeline não depende de um orquestrador específico. Os comandos de referência usam Docker Swarm; a plataforma de produção pode ser trocada sem alterar os contratos abaixo.

| Script | Entrada | O que faz | Critério de sucesso |
|---|---|---|---|
| `scripts/deploy.sh <env> <sha>` | Ambiente e commit | Migração expand, atualização da imagem, rolling update | Serviço saudável em 2 réplicas |
| `scripts/smoke.sh <baseUrl>` | URL pública | Testa home, busca, ficha, healthcheck e admin | Todos os checks em `200` |
| `scripts/rollback.sh <env> <sha>` | Ambiente e commit anterior | Volta a imagem e, se necessário, aplica migração reversa | Smoke passa na versão anterior |
| `scripts/reprocess_dlq.py` | Fila e limite | Reenfileira mensagens da DLQ | Nenhuma mensagem nova na DLQ |

```bash
# deploy com rolling update e rollback automático em caso de falha
docker service update \
  --image "ghcr.io/org/sosp/api:${SHA}" \
  --update-order start-first \
  --update-parallelism 1 \
  --update-failure-action rollback \
  --with-registry-auth \
  sosp_api
```

```bash
# smoke mínimo
curl -fsS https://sosp.gov.br/api/v1/health
curl -fsS "https://sosp.gov.br/api/v1/services?q=certidao&page=1&pageSize=10"
curl -fsS https://sosp.gov.br/servicos/7f3c2a10-0f6e-4a7b-9c1d-2e3f4a5b6c7d
```

### 5.4 Migrações no pipeline

| Etapa | Comando | Regra |
|---|---|---|
| Validar | `python manage.py makemigrations --check --dry-run` | Falha se houver migração não versionada |
| Aplicar | `python manage.py migrate --noinput` | Roda antes do deploy da API |
| Verificar | `python manage.py migrate --plan` | Nenhuma operação destrutiva inesperada |
| Reverter | `python manage.py migrate <app> <migração>` | Testado em staging antes do release |

**Regra de compatibilidade:** a migração `expand` entra antes do código novo; a `contract` só entra depois que nenhuma réplica antiga está em uso. Nunca renomear ou remover coluna no mesmo deploy que altera o código.

### 5.5 Zero-downtime

```mermaid
sequenceDiagram
    autonumber
    participant CI as Pipeline
    participant DB as PostgreSQL
    participant LB as Proxy
    participant A1 as API antiga
    participant A2 as API nova

    CI->>DB: Migração expand compatível
    CI->>A2: Sobe réplica nova
    A2->>A2: Healthcheck /api/v1/health
    CI->>LB: Adiciona A2 ao balanceamento
    LB->>A2: Tráfego canário 10%
    CI->>CI: Monitora 5 min
    CI->>LB: Remove A1 do balanceamento
    A1->>A1: Drena requisições em andamento
    CI->>A1: Encerra réplica antiga
    CI->>DB: Migração contract em release posterior
```

**Condições para o deploy prosseguir**

1. Migração `expand` aplicada sem lock maior que 5 s.
2. Réplica nova responde `200` no healthcheck por 3 tentativas consecutivas.
3. Taxa de erro canário < 1% e p95 estável por 5 minutos.
4. Nenhum alerta SEV1 ou SEV2 aberto.

### 5.6 Rollback

| Cenário | Ação | Tempo alvo |
|---|---|---|
| Erro de aplicação sem migração | Voltar imagem anterior | 5 min |
| Migração `expand` problemática | Voltar imagem e manter coluna nova | 10 min |
| Migração destrutiva | Restaurar backup e voltar imagem | 4 h |
| Falha de configuração | Reverter variável no secret manager e reiniciar | 10 min |
| Falha do portal | Voltar imagem do portal | 5 min |

```bash
./scripts/rollback.sh production "$(git describe --tags --abbrev=0 HEAD^)"
```

**Regra:** rollback não é improviso. O script é testado em staging a cada release e o tempo é registrado no checklist.

### 5.7 Ambientes

| Ambiente | Propósito | Dados | Deploy | Acesso |
|---|---|---|---|---|
| Local | Desenvolvimento | Fixtures sintéticas | Manual | Desenvolvedor |
| CI | Teste automatizado | Banco efêmero | Pipeline | Ninguém |
| Staging | Homologação e demo | Cópia anonimizada ou fixtures | Automático no merge em `develop` | Equipe e avaliadores |
| Produção | Uso real | Dados reais | Aprovação manual | Operação |

### 5.8 Checklist de release

| # | Item | Responsável |
|---|---|---|
| 1 | Changelog gerado a partir dos commits | Autor |
| 2 | Migração revisada e reversível | Back-end |
| 3 | Contrato OpenAPI validado | Back-end |
| 4 | E2E verde em Chromium, Firefox e mobile | QA |
| 5 | axe-core sem violação crítica | Front-end |
| 6 | Carga de referência executada quando há mudança de query | Back-end |
| 7 | Feature flags conferidas | Produto |
| 8 | Runbook atualizado quando há novo alerta | Plantão |
| 9 | Rollback ensaiado em staging | DevOps |
| 10 | Comunicação de release enviada | Gestão |

---

## 6. Observabilidade

### 6.1 Sinais

| Sinal | O que responde | Ferramenta | Retenção |
|---|---|---|---|
| Métricas | O sistema está saudável e rápido? | Prometheus + Grafana | 90 dias |
| Logs | O que aconteceu nesta requisição? | Coletor do provedor | 30 dias |
| Traces | Onde o tempo foi gasto? | OpenTelemetry + Sentry | 7 dias |
| Erros | Qual exceção quebrou a jornada? | Sentry | 90 dias |
| RUM | Como o cidadão percebeu? | Web Vitals + endpoint próprio | 90 dias |
| Healthchecks | A réplica pode receber tráfego? | `/api/v1/health` e `/health` | Tempo real |

**Regra:** todo log de aplicação é JSON estruturado com `timestamp`, `level`, `service`, `traceId`, `route`, `status`, `durationMs` e `userId` pseudonimizado. Nenhum log contém CPF, e-mail, telefone, endereço ou token (RNF-12).

### 6.2 SLIs e SLOs

| SLI | Definição | SLO | Janela | Error budget |
|---|---|---|---|---|
| Disponibilidade | Requisições sem 5xx ÷ total | ≥ 99,0% | Dias úteis, 08h–18h | 2,2 h/mês |
| Latência de busca | p95 de `GET /services` | ≤ 2,5 s | 28 dias | 5% das requisições |
| Latência de ficha | p95 de `GET /services/{id}` | ≤ 2,0 s | 28 dias | 5% das requisições |
| Latência de PDF | p95 de geração | ≤ 4,0 s | 28 dias | 5% dos jobs |
| Taxa de erro | 5xx ÷ total | ≤ 1,0% | 28 dias | 1% |
| Sucesso de PDF | Jobs concluídos ÷ enfileirados | ≥ 99,0% | 28 dias | 1% |
| Atraso de fila | Idade da mensagem mais antiga | ≤ 60 s | 28 dias | 5 min |
| Frescor de backup | Último backup bem-sucedido | ≤ 24 h | Contínuo | 0 |
| Web Vitals LCP | p75 mobile | ≤ 2,5 s | 28 dias | 25% das sessões |

**Política de error budget:** se 50% do budget for consumido em 7 dias, features são congeladas e a prioridade passa a ser confiabilidade. Se 100% for consumido, o release exige aprovação da gestão.

### 6.3 Dashboards

| Dashboard | Painéis | Público |
|---|---|---|
| Visão do cidadão | Disponibilidade, p95/p99 de busca e ficha, LCP, INP, CLS | Produto e engenharia |
| API | Requisições por rota, 4xx/5xx, latência, conexões, pool | Engenharia |
| Banco | CPU, IOPS, conexões, locks, replicação, queries lentas | Engenharia |
| Filas | Profundidade por fila, idade da mensagem, falhas, DLQ | Engenharia e plantão |
| Jornada | Busca → ficha → guia → agendamento → protocolo | Produto |
| Segurança | Login falho, bloqueios, 403, uploads rejeitados | Segurança |

### 6.4 Alertas

| Alerta | Condição | Janela | Severidade | Dono | Runbook |
|---|---|---|---|---|---|
| API 5xx alto | `5xx / total > 1%` | 5 min | SEV2 | Back-end | 7.3.1 |
| Busca lenta | `p95 > 2,5 s` | 10 min | SEV3 | Back-end | 7.3.1 |
| Ficha lenta | `p95 > 2,0 s` | 10 min | SEV3 | Back-end | 7.3.1 |
| PDF falhando | `falhas / jobs > 1%` | 15 min | SEV3 | Back-end | 7.3.4 |
| Fila acumulada | `profundidade > 100` | 10 min | SEV3 | Back-end | 7.3.4 |
| DLQ com mensagem | `dlq > 0` | 1 min | SEV3 | Back-end | 7.3.4 |
| PostgreSQL indisponível | `pg_up == 0` | 1 min | SEV1 | Plantão | 7.3.2 |
| Conexões esgotando | `conexões > 80%` | 10 min | SEV2 | Plantão | 7.3.2 |
| Réplica atrasada | `lag > 30 s` | 10 min | SEV2 | Plantão | 7.3.2 |
| Redis indisponível | `redis_up == 0` | 1 min | SEV2 | Plantão | 7.3.3 |
| Gov.br falhando | `erros OIDC > 10%` | 5 min | SEV3 | Back-end | 7.3.5 |
| Storage falhando | `erros S3 > 5%` | 5 min | SEV2 | Plantão | 7.3.6 |
| Disco acima de 80% | `disk_used > 80%` | 15 min | SEV3 | Infra | 7.3.7 |
| Certificado expirando | `dias_para_expirar < 21` | Diário | SEV3 | Infra | 7.3.8 |
| Backup falhou | `backup_success == 0` | 1 execução | SEV2 | Plantão | 8.4 |
| Web Vitals ruim | `LCP p75 > 2,5 s` | 6 h | SEV4 | Front-end | 6.3 |

**Regra:** todo alerta tem dono, limiar, janela e link para o runbook. Alerta sem ação é ruído e será removido.

### 6.5 Logs e privacidade

| Campo | Exemplo | PII | Regra |
|---|---|---|---|
| `traceId` | `4bf92f35...` | Não | Correlaciona requisição e erro |
| `route` | `/api/v1/services` | Não | Rota normalizada, sem query sensível |
| `status` | `200` | Não | — |
| `durationMs` | `183` | Não | — |
| `userId` | hash de 16 caracteres | Pseudonimizado | Nunca o CPF |
| `searchTerm` | `certidao` | Potencial | Só em `searchQueryLog`, nunca no log de aplicação |
| `cpf` | — | Sim | Proibido no log; mascarado quando inevitável |
| `email` | — | Sim | Proibido no log |
| `authorization` | — | Sim | Proibido no log |

```python
# common/logging.py
import logging
import re

PII_PATTERNS = [
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "[EMAIL]"),
    (re.compile(r"\b\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b"), "[PHONE]"),
]


class PiiFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern, replacement in PII_PATTERNS:
            message = pattern.sub(replacement, message)
        record.msg = message
        record.args = ()
        return True
```

### 6.6 Monitoração sintética

| Check | Frequência | Origem | Critério |
|---|---|---|---|
| Home do portal | 1 min | Duas regiões | `200` e título correto |
| Busca `certidao` | 5 min | Duas regiões | `200` e ao menos 1 item |
| Ficha de serviço fixo | 5 min | Duas regiões | `200` e bloco de custo |
| Healthcheck da API | 30 s | Load balancer | `200` e banco `ok` |
| Login interno | 15 min | Uma região | Sessão criada e logout |
| Admin | 5 min | Uma região | `200` na tela de login |

---

## 7. Runbook de operação

### 7.1 Severidade e prazos

| Severidade | Definição | Exemplo | Resposta | Atualização | Resolução |
|---|---|---|---|---|---|
| SEV1 | Serviço indisponível ou perda de dados | Banco fora, todos os agendamentos falhando | 15 min | A cada 30 min | 4 h |
| SEV2 | Função crítica degradada | Agendamento falha para parte dos usuários | 30 min | A cada 1 h | 8 h |
| SEV3 | Degradação sem bloqueio total | PDF lento, fila acumulada | 2 h | A cada 4 h | 2 dias |
| SEV4 | Melhoria ou risco baixo | Web Vitals acima da meta | 1 dia útil | Diária | 1 sprint |

**Plantão:** uma pessoa por semana, com escalonamento para back-end, infra e gestão. O contato fica no canal `#sosp-incidentes`.

### 7.2 Checklist de incidente

| # | Ação | Quando |
|---|---|---|
| 1 | Declarar o incidente e a severidade | Imediatamente |
| 2 | Abrir canal e nomear o incident commander | SEV1 e SEV2 |
| 3 | Registrar início em UTC e o sintoma | Imediatamente |
| 4 | Verificar o dashboard e o healthcheck | Primeiros 5 min |
| 5 | Identificar a última mudança (deploy, config, migração) | Primeiros 10 min |
| 6 | Aplicar mitigação, não a correção definitiva | Assim que possível |
| 7 | Comunicar usuários e stakeholders | Conforme severidade |
| 8 | Confirmar recuperação com smoke test | Antes de encerrar |
| 9 | Registrar timeline e evidências | Durante o incidente |
| 10 | Agendar postmortem em até 5 dias úteis | Após estabilizar |

### 7.3 Playbooks

#### 7.3.1 API com 5xx ou latência alta

**Sintoma:** alerta de `5xx > 1%` ou `p95 > 2,5 s`.

1. Conferir dashboard da API por rota e por status.
2. Verificar o último deploy: `docker service ps sosp_api`.
3. Se o erro começou após deploy, executar rollback (5.6).
4. Se não houve deploy, verificar banco, Redis e dependências externas.
5. Coletar `traceId` de uma requisição afetada e abrir o trace no Sentry.
6. Se a causa for query lenta, identificar no dashboard do banco e aplicar `EXPLAIN (ANALYZE, BUFFERS)`.
7. Mitigar com cache, rate limit ou desligamento de feature flag.
8. Confirmar recuperação com `scripts/smoke.sh`.

#### 7.3.2 PostgreSQL indisponível ou lento

**Sintoma:** `pg_up == 0`, conexões esgotadas, query lenta ou projeto Supabase pausado.

1. Verificar o status do projeto Supabase no painel (projetos gratuitos pausam após inatividade; reativar clicando em "Restore").
2. Conferir o dashboard de banco no Supabase para conexões ativas, locks e query lenta.
3. Verificar logs do PostgreSQL no painel ou pelo `pg_stat_activity` via conexão direta.
4. Se o problema for esgotamento de conexões do pooler:
   - Verificar `pg_stat_activity` — conta com `state = 'idle in transaction'`.
   - Reduzir `DATABASE_CONN_MAX_AGE` ou workers ociosos.
   - Em último caso, alternar para Transaction pooler (porta 6543) configurando `DATABASE_DISABLE_SERVER_SIDE_CURSORS=true` e `DATABASE_CONN_MAX_AGE=0`.
5. Se houver lock, identificar com `pg_stat_activity` e encerrar a sessão bloqueadora com cautela.
6. Validar integridade com `SELECT count(*) FROM schedulingAppointment;` e smoke test.
7. Registrar o horário do incidente e o RPO real.
8. Confirmar recuperação com `scripts/smoke.sh`.

```sql
-- Sessões bloqueando outras
SELECT pid, usename, state, wait_event_type, wait_event, query
FROM pg_stat_activity
WHERE state <> 'idle'
ORDER BY query_start;

-- Conexões ativas por usuário
SELECT usename, count(*) AS conexoes
FROM pg_stat_activity
GROUP BY usename
ORDER BY conexoes DESC;
```

#### 7.3.3 Redis indisponível

**Sintoma:** `redis_up == 0`, sessões perdidas e filas paradas.

1. Verificar o serviço e o disco.
2. Se for cache, a API continua com latência maior; se for sessão, usuários precisam relogar.
3. Se for broker, workers param; reiniciar Redis e workers na ordem.
4. Confirmar que nenhuma mensagem foi perdida com `LLEN` das filas.
5. Comunicar que sessões podem ter expirado.

#### 7.3.4 Fila acumulada, PDF falhando ou DLQ

**Sintoma:** profundidade > 100, falha de PDF > 1% ou mensagem na DLQ.

1. Verificar workers ativos: `celery -A config inspect active`.
2. Conferir a fila afetada e a taxa de consumo.
3. Se o worker estiver morto, subir nova réplica.
4. Se a causa for dependência externa, pausar o consumo e aplicar backoff.
5. Inspecionar a DLQ com `--dry-run` antes de reprocessar.
6. Reprocessar em lote limitado e monitorar.
7. Se o job for inválido, descartar com registro e corrigir o produtor.

```bash
celery -A config inspect active_queues
redis-cli -u "$REDIS_URL" LLEN dlq.pdf
python scripts/reprocess_dlq.py --queue pdf --limit 100 --dry-run
python scripts/reprocess_dlq.py --queue pdf --limit 100
```

#### 7.3.5 Gov.br indisponível (v2.0)

**Sintoma:** erros OIDC > 10%, cidadão não consegue entrar (aplicável apenas na v2.0, quando `FEATURE_GOVBR_INTEGRATION_ENABLED=true`).

1. Conferir o status oficial do Gov.br.
2. Confirmar que o problema não é credencial ou relógio do servidor.
3. Exibir a página de indisponibilidade com orientação e canal de contato.
4. Manter o login local CPF + senha como fallback.
5. Quando o provedor voltar, validar um login completo e o retorno à ação.
6. Não criar conta local de cidadão como contorno: isso quebraria o D10.

#### 7.3.6 S3/MinIO indisponível

**Sintoma:** upload e PDF falham com erro de storage.

1. Verificar o serviço e as credenciais.
2. Confirmar que o bucket existe e que a política não mudou.
3. Se o problema for URL assinada, conferir `SIGNED_URL_TTL_SECONDS` e o relógio.
4. Reenfileirar jobs de PDF após a recuperação.
5. Comunicar que anexos podem estar temporariamente indisponíveis.

#### 7.3.7 Disco cheio

**Sintoma:** `disk_used > 80%` ou falha de escrita.

1. Identificar o maior consumidor: logs, backups, imagens ou dados.
2. Remover arquivos temporários e rotações antigas com segurança.
3. Mover backups para o storage de objetos.
4. Aumentar o volume se a tendência for estrutural.
5. Revisar a política de retenção.

#### 7.3.8 Certificado TLS expirado ou expirando

**Sintoma:** navegador alerta conexão insegura ou `dias_para_expirar < 21`.

1. Renovar o certificado no provedor.
2. Validar a cadeia completa com `openssl s_client -connect sosp.gov.br:443 -servername sosp.gov.br`.
3. Confirmar HSTS e redirecionamento.
4. Atualizar o monitoramento.

#### 7.3.9 Deploy com defeito

**Sintoma:** erro ou latência começa logo após um deploy.

1. Confirmar a correlação por horário e por `GIT_SHA`.
2. Executar `scripts/rollback.sh` para a versão anterior.
3. Se a migração for incompatível, restaurar o backup e validar.
4. Congelar novos deploys até o postmortem.
5. Registrar a versão afetada e o tempo de exposição.

#### 7.3.10 Incidente de dados ou pedido LGPD

**Sintoma:** acesso indevido, exposição, perda ou pedido de titular.

1. Acionar o encarregado de dados (DPO) imediatamente.
2. Isolar o acesso e preservar evidências.
3. Identificar titulares e categorias de dados afetados.
4. Avaliar risco e prazo de comunicação à ANPD e aos titulares.
5. Registrar em `auditDataSubjectRequest` e no canal de incidentes.
6. Não apagar logs ou evidências antes da conclusão da análise.

### 7.4 Comunicação

| Momento | Canal | Conteúdo |
|---|---|---|
| Abertura SEV1/SEV2 | `#sosp-incidentes` | Sintoma, impacto, severidade, incident commander |
| Atualização | `#sosp-incidentes` | O que mudou, próximo passo, ETA |
| Mitigação | `#sosp-incidentes` e status page | O que foi feito e o que ainda está degradado |
| Encerramento | `#sosp-incidentes` | Duração, causa provável, link do postmortem |

**Modelo de mensagem**

```text
[SEV2] Agendamento com erro intermitente
Início: 2026-10-29 14:05 UTC
Impacto: parte dos cidadãos recebe 409 ao confirmar slot.
Causa provável: contenção no lock de slot após aumento de tráfego.
Mitigação: réplica adicional do worker e rollback da versão 1.4.2.
Próxima atualização: 14:35 UTC.
```

---

## 8. Backup e restore

### 8.1 Política

| Item | Valor | Origem |
|---|---|---|
| RPO exigido | ≤ 24 h | RNF-07 |
| RPO alcançado | ≤ 15 min com WAL archiving | Arquitetura |
| RTO exigido | ≤ 4 h | RNF-07 |
| RTO testado | ≤ 2 h | Ensaio mensal |
| Backup completo | Diário, 02:00 BRT | RNF-07 |
| Retenção diária | 30 dias | RNF-07 |
| Retenção mensal | 12 meses | Política interna |
| Restore de teste | Mensal, em ambiente isolado | RNF-07 |
| Criptografia | AES-256 em repouso e TLS em trânsito | RS-02 |
| Local | Região primária + cópia em região distinta | Continuidade |

### 8.2 Rotina

```bash
#!/usr/bin/env bash
# scripts/backup.sh
set -euo pipefail

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="/backups/sosp-${STAMP}.dump"

pg_dump \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="${TARGET}" \
  "${DATABASE_DIRECT_URL}"

pg_restore --list "${TARGET}" > "${TARGET}.list"
sha256sum "${TARGET}" > "${TARGET}.sha256"

aws s3 cp "${TARGET}" "s3://${BACKUP_BUCKET}/daily/${STAMP}.dump" \
  --sse AES256
aws s3 cp "${TARGET}.sha256" "s3://${BACKUP_BUCKET}/daily/${STAMP}.dump.sha256"

find /backups -name 'sosp-*.dump' -mtime +30 -delete
```

**Verificação automática:** o job só é considerado bem-sucedido se o `pg_restore --list` retornar as 34 tabelas e o checksum conferir.

**Nota Supabase:** o script de backup usa `DATABASE_DIRECT_URL` (conexão direta, não o pooler), porque o Session pooler não é indicado para `pg_dump` — o dump pode ser interrompido ou gerar snapshot inconsistente. Em staging e produção, a variável `BACKUP_BUCKET` aponta para um storage externo ao Supabase (bucket S3 independente). O backup nativo do Supabase é complementar, não substituto.

### 8.3 Restore

```bash
# 1. Baixar e conferir o checksum
aws s3 cp "s3://${BACKUP_BUCKET}/daily/${STAMP}.dump" /restore/
sha256sum -c "/restore/${STAMP}.dump.sha256"

# 2. Criar banco isolado
createdb -h localhost -U postgres sosp_restore

# 3. Restaurar
pg_restore \
  --no-owner \
  --no-privileges \
  --dbname=sosp_restore \
  /restore/${STAMP}.dump

# 4. Validar contagens mínimas
psql -h localhost -U postgres -d sosp_restore -c "
SELECT
  (SELECT count(*) FROM catalogservice) AS servicos,
  (SELECT count(*) FROM schedulingappointment) AS agendamentos,
  (SELECT count(*) FROM schedulingprotocol) AS protocolos,
  (SELECT count(*) FROM auditEvent) AS auditoria;
"

# 5. Smoke funcional
DATABASE_URL=postgres://postgres@localhost:5432/sosp_restore ./scripts/smoke.sh http://localhost:8000
```

**Point-in-time recovery:** com WAL archiving, o restore pode parar em um instante anterior ao incidente:

```bash
pg_restore --dbname=sosp_pitr /backups/base.dump
# aplicar WAL até o instante desejado no recovery.conf do provedor
```

### 8.4 Ensaio mensal de restore

| # | Passo | Evidência |
|---|---|---|
| 1 | Escolher o backup mais recente | Nome e timestamp |
| 2 | Restaurar em ambiente isolado | Log do `pg_restore` |
| 3 | Conferir contagens por tabela | Consulta assinada |
| 4 | Rodar smoke de busca, ficha e agendamento | Relatório do script |
| 5 | Medir tempo total | Início e fim em UTC |
| 6 | Comparar com RTO de 4 h | Resultado |
| 7 | Registrar falhas e ações | Issue com dono e prazo |
| 8 | Arquivar evidência | Link no repositório de operação |

**Critério de sucesso:** restore completo em até 4 h, contagens compatíveis e smoke verde. Ensaio que falha gera incidente SEV2.

### 8.5 Object storage

| Item | Regra |
|---|---|
| Versionamento | Ativado no bucket de anexos e PDFs |
| Ciclo de vida | PDFs expiram em 30 dias; anexos seguem a retenção do protocolo |
| Exclusão | Lógica no banco; objeto só é removido após o prazo legal |
| Acesso | URL assinada com 5 min de validade |
| Criptografia | SSE-S3 ou SSE-KMS |
| Backup | Replicação para região distinta |

### 8.6 Evidências

| Evidência | Onde fica | Retenção |
|---|---|---|
| Log do backup diário | Ferramenta de CI/operação | 90 dias |
| Checksum | Bucket de backup | 12 meses |
| Relatório de restore | Repositório de operação | 5 anos |
| Incidente de restore | Postmortem | 5 anos |

---

## 9. Postmortem sem culpa

### 9.1 Princípios

1. **Pessoas não são o problema; processos e sistemas são.** O postmortem busca a condição que permitiu o erro, não o culpado.
2. **Timeline factual.** Horários em UTC, com fonte de cada informação.
3. **Sem eufemismo.** "Fila travou" é melhor que "houve uma instabilidade".
4. **Ação com dono e prazo.** Item sem responsável não é ação.
5. **Aprendizado compartilhado.** O documento é público para a equipe.

### 9.2 Template

```markdown
# Postmortem — <título curto>

- **Data do incidente:** AAAA-MM-DD
- **Severidade:** SEV1 | SEV2 | SEV3 | SEV4
- **Duração:** HH:MM (UTC)
- **Detectado por:** alerta | usuário | equipe
- **Incident commander:** <nome>
- **Autores:** <nomes>
- **Status:** rascunho | revisado | aprovado

## Impacto

- Usuários afetados: <número ou percentual>
- Funcionalidades afetadas: <lista>
- Perda de dados: <sim/não, com detalhe>
- Receita ou prazo: <impacto>

## Timeline (UTC)

| Hora | Evento |
|---|---|
| 14:05 | Alerta de 5xx dispara |
| 14:07 | Plantão assume e declara SEV2 |
| 14:12 | Rollback iniciado |
| 14:20 | Smoke verde e incidente mitigado |

## Causa raiz

<Descrição técnica da causa, com evidência: trace, log, query, diff.>

## Fatores contribuintes

- <Fator 1>
- <Fator 2>

## O que funcionou

- <Ponto 1>
- <Ponto 2>

## O que não funcionou

- <Ponto 1>
- <Ponto 2>

## Ações

| # | Ação | Tipo | Dono | Prazo | Status |
|---|---|---|---|---|---|
| 1 | <Ação> | preventiva | <nome> | AAAA-MM-DD | aberta |
| 2 | <Ação> | detecção | <nome> | AAAA-MM-DD | aberta |
| 3 | <Ação> | mitigação | <nome> | AAAA-MM-DD | aberta |

## Lições

<O que a equipe aprendeu e o que muda no runbook.>
```

### 9.3 Exemplo preenchido

```markdown
# Postmortem — Fila de PDF travada após deploy

- **Data do incidente:** 2026-10-22
- **Severidade:** SEV3
- **Duração:** 1 h 12 min (UTC)
- **Detectado por:** alerta de profundidade de fila
- **Incident commander:** Renata (back-end)
- **Status:** aprovado

## Impacto

- 38 cidadãos não conseguiram baixar o PDF de orientação no prazo de 5 s.
- Nenhum dado foi perdido; os jobs ficaram na fila e foram reprocessados.
- O agendamento não foi afetado.

## Timeline (UTC)

| Hora | Evento |
|---|---|
| 13:40 | Deploy da versão 1.4.2 |
| 13:52 | Alerta de fila > 100 dispara |
| 13:55 | Plantão confirma worker consumindo 0 msg/min |
| 14:02 | Identificado import circular no novo módulo de template |
| 14:08 | Rollback para 1.4.1 |
| 14:20 | Fila drenada e DLQ reprocessada |
| 14:52 | Monitoração estável e incidente encerrado |

## Causa raiz

O novo módulo de template importava `notifications.models` no carregamento do worker, criando import circular que impedia o worker de iniciar. O healthcheck do worker não fazia parte do deploy, então o pipeline considerou o deploy bem-sucedido.

## Fatores contribuintes

- O worker não tinha healthcheck no pipeline.
- O teste de importação não cobria o carregamento do worker.
- O alerta de fila demorou 12 minutos para disparar.

## O que funcionou

- O rollback foi executado em 6 minutos.
- A DLQ preservou os jobs e permitiu reprocessamento.
- A comunicação no canal foi clara.

## O que não funcionou

- O deploy não validou o worker.
- O teste de contrato não cobria import de tarefa.
- O alerta de fila tinha janela longa.

## Ações

| # | Ação | Tipo | Dono | Prazo | Status |
|---|---|---|---|---|---|
| 1 | Adicionar healthcheck do worker no deploy | detecção | DevOps | 2026-10-29 | concluída |
| 2 | Teste de importação de todas as tarefas Celery | preventiva | Back-end | 2026-11-05 | concluída |
| 3 | Reduzir janela do alerta de fila para 5 min | detecção | Back-end | 2026-11-05 | concluída |
| 4 | Documentar DLQ no runbook | mitigação | Plantão | 2026-10-29 | concluída |

## Lições

Deploy de aplicação com worker exige validação do worker, não apenas da API. O runbook passou a incluir o comando de verificação de fila antes do smoke.
```

### 9.4 Acompanhamento das ações

| Prazo | Regra |
|---|---|
| Ações preventivas | 30 dias |
| Ações de detecção | 15 dias |
| Ações de mitigação | 7 dias |
| Revisão de eficácia | 60 dias após a conclusão |

**Regra:** ação vencida aparece no dashboard de engenharia e é tratada como débito técnico prioritário.

---

## 10. Feature flags e ambientes

| Flag | Padrão | O que liga | Requisito | Expiração |
|---|---|---|---|---|
| `FEATURE_REVIEWS_ENABLED` | `false` | Botão e fluxo de avaliação | RF-10 | v2.0 |
| `FEATURE_NOTIFICATION_CENTER_ENABLED` | `false` | Central de preferências de notificação | RF-13 | v2.0 |
| `FEATURE_PUSH_ENABLED` | `false` | Web Push no navegador | RF-13 | v2.0 |
| `FEATURE_SMS_ENABLED` | `false` | Canal SMS | RF-13 | Fase 3 |
| `FEATURE_WHATSAPP_ENABLED` | `false` | Canal WhatsApp | RF-13 | Fase 3 |
| `FEATURE_REPORTS_EXPORT` | `true` | Exportação CSV/PDF de relatórios | RF-14 | Não expira (MVP)
| `FEATURE_GOVBR_INTEGRATION_ENABLED` | `false` | Fluxo OIDC do Gov.br | RF-02 | v2.0 |

**Regras**

1. Flag nasce desligada, com dono, motivo e data de expiração.
2. Flag não substitui autorização: rota desligada retorna `404` (recurso inexistente no escopo) ou `403` (operação desabilitada), conforme documentado no OpenAPI.
3. Flag é avaliada no servidor; o cliente não decide regra de negócio.
4. Flag removida junto com o código morto após a estabilização.
5. Toda flag aparece no `.env.example` e no Pilar 1 (D5, D7, D13).

---

## 11. Rastreabilidade e definição de pronto operacional

### 11.1 Requisito → prática de engenharia

| Requisito | Prática | Onde |
|---|---|---|
| RNF-04 desempenho | k6, SLO de p95/p99, alerta de latência | 4.7, 6.2, 6.4 |
| RNF-05 compatibilidade | Playwright em Chromium, Firefox e mobile; SLO de 99% | 4.5, 6.2 |
| RNF-06 acessibilidade | axe-core no E2E, checklist manual | 4.5, 4.9 |
| RNF-07 backup | Backup diário, retenção 30 dias, restore mensal | 8 |
| RNF-08 segurança | Secrets, headers, rate limit, dependências | 2, 4.8, 5 |
| RNF-09 observabilidade | Métricas, logs, traces, alertas | 6 |
| RNF-10 manutenibilidade | Cobertura 80/70, lint, complexidade | 3.4, 4.9 |
| RNF-11 portabilidade | Docker, compose e deploy agnóstico | 1.3, 5.3 |
| RNF-12 privacidade | Filtro de PII, fixtures sintéticas, retenção | 4.10, 6.5 |
| RS-01 CPF único | Teste de constraint e autorização | 4.2, 4.3 |
| RS-02 senha e sessão | Argon2id, bloqueio, sessão de 30 min | 4.8 |
| RS-03 acesso por perfil | Teste de autorização por papel | 4.8 |
| RS-04 anexo malicioso | Validação de MIME, tamanho e antivírus | 4.8 |
| RS-05 histórico | Exclusão lógica e restore testado | 8.4 |
| RF-06 busca e ficha | E2E, contrato, carga e estado vazio | 4.3, 4.5, 4.7 |
| RF-08 agendamento | Teste de concorrência e idempotência | 4.2, 4.3 |
| RF-09 protocolo | E2E de linha do tempo e 404 de terceiro | 4.5 |

### 11.2 Definição de pronto operacional

Um release só é considerado pronto para produção quando todos os itens são verdadeiros.

| # | Critério | Evidência |
|---|---|---|
| 1 | Pipeline completo verde | GitHub Actions |
| 2 | Cobertura ≥ 80% no back-end e ≥ 70% no portal | Relatório de cobertura |
| 3 | Contrato OpenAPI validado | Job de contrato |
| 4 | Migração `expand` aplicada e `contract` planejada | Plano de migração |
| 5 | Smoke de staging verde | `scripts/smoke.sh` |
| 6 | Smoke de produção verde após deploy | `scripts/smoke.sh` |
| 7 | Dashboards com dados do novo release | Grafana |
| 8 | Alertas revisados e com dono | 6.4 |
| 9 | Backup recente e restore de teste em dia | 8.4 |
| 10 | Rollback ensaiado e documentado | 5.6 |
| 11 | Feature flags conferidas | 10 |
| 12 | Runbook atualizado | 7 |
| 13 | Changelog e notas de release publicados | Repositório |
| 14 | Nenhum alerta SEV1 ou SEV2 aberto | Painel de incidentes |
| 15 | Postmortem anterior com ações concluídas ou justificadas | 9.4 |

---

**Anterior:** [Pilar 4 — Modelagem de Dados e Contratos de API](04-data-api.md) · **Índice:** [README](README.md)
