# SOSP — Guia de Implantação e Runbooks de Nuvem
## Cloudflare Workers (Frontend OpenNext) + Render Web Service (Backend) + Supabase (Database)

> **Documento Oficial de Engenharia e Operações (Pilar 5)**
> **Modalidade Oficial Frontend:** Cloudflare Workers com `@opennextjs/cloudflare` (Workers Builds via GitHub).
> **Modalidade Oficial Backend:** Render Web Service (Gunicorn + Django 5 REST Framework).
> **Banco de Dados:** Supabase Managed PostgreSQL 17.11 (Isolamento RLS + HMAC).

---

## 1. Visão Geral da Arquitetura de Nuvem

```mermaid
flowchart LR
    Citizen["Cidadão / Servidor\n(Navegador HTTPS)"]
    CF["Cloudflare Anycast CDN & Workers\n(OpenNext: portal/.open-next/worker.js)\nsosp-portal.workers.dev"]
    Render["Render Web Service\n(backend/ via Gunicorn)\nsosp-backend-staging.onrender.com"]
    Supa["Supabase Managed PostgreSQL 17.11\n(aws-1-sa-east-1.pooler.supabase.com:5432)\nsosp_runtime_app (RLS + HMAC)"]

    Citizen -->|HTTPS / WAF Anycast| CF
    Citizen -->|API REST /api/v1 (Bearer Token)| Render
    Render -->|TLS verify-full / Porta 5432| Supa
```

---

## 2. Configuração do Backend no Render

### 2.1 Criação do Serviço via Blueprint (`render.yaml`) ou Dashboard
- **Tipo de Serviço:** Web Service
- **Nome do Serviço:** `sosp-backend-staging`
- **Ambiente:** Python 3.13
- **Root Directory:** `backend`
- **Build Command:** `./render-build.sh` (executável: `pip install -r requirements.txt`, `manage.py check`, `collectstatic`)
- **Start Command:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -`
- **Health Check Path:** `/api/v1/health` (resposta esperada: HTTP 200 `{"status": "healthy", ...}`)
- **Plano:** `free` (staging/homologação, sem custo e sem cartão). Efeito colateral: o serviço hiberna após ~15 min sem tráfego e a primeira requisição após a hibernação sofre *cold start* de ~30–60 s. Para uso contínuo de produção, avaliar plano pago em tarefa própria.

### 2.2 Variáveis de Ambiente no Render

| Variável | Valor para Staging | Sensível? | Descrição |
|---|---|:---:|---|
| `PYTHON_VERSION` | `3.13.0` | Não | Versão do interpretador Python |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Não | Módulo de configurações seguras |
| `DEBUG` | `false` | Não | Desativa depuração em produção |
| `ALLOWED_HOSTS` | `sosp-backend-staging.onrender.com,localhost,127.0.0.1` | Não | Hosts permitidos |
| `CORS_ALLOWED_ORIGINS` | `https://sosp-portal.workers.dev,https://sosp-portal-staging.workers.dev` | Não | Origens dos Cloudflare Workers de staging (produção não é permitida aqui) |
| `CSRF_TRUSTED_ORIGINS` | `https://sosp-portal.workers.dev,https://sosp-portal-staging.workers.dev` | Não | Origens confiáveis para CSRF em staging (produção não é permitida aqui) |
| `REPOSITORY_BACKEND` | `orm` | Não | Persistência real PostgreSQL via Django ORM |
| `DB_ENGINE` | `postgresql` | Não | Engine de banco de dados |
| `DB_HOST` | `aws-1-sa-east-1.pooler.supabase.com` | Não | Pooler Session do Supabase |
| `DB_PORT` | `5432` | Não | Porta do pooler |
| `DB_NAME` | `postgres` | Não | Nome do banco de dados |
| `DB_USER` | `sosp_runtime_app.cidtcgfowvgwgggvhbym` | Não | Usuário de runtime de menor privilégio |
| `DB_SSLMODE` | `verify-full` | Não | TLS estrito com validação de CA |
| `DB_SSLROOTCERT` | `/etc/secrets/supabase-ca.crt` | Não | CA raiz do Supabase, montada via **Secret File** do Render (ver §2.3) |
| `DB_PASSWORD` | `[DEFINIDA_PELO_OPERADOR]` | **SIM** | Senha de runtime (`sync: false`) |
| `DB_HMAC_SECRET_KEY` | `[DEFINIDA_PELO_OPERADOR]` | **SIM** | Chave HMAC de 32+ caracteres (`sync: false`) |
| `SECRET_KEY` | `[GERADA_PELO_OPERADOR]` | **SIM** | Chave criptográfica Django (`sync: false`) |

> [!CAUTION]
> **NUNCA execute `python manage.py migrate` automaticamente durante o build ou startup no Render.**
> O schema físico já foi provisionado (4C.2/4D.2) e possui políticas RLS e grants rigorosos. Qualquer evolução de banco exige procedimento administrativo supervisionado.

### 2.3 Secret File obrigatório: CA raiz do Supabase

O pooler do Supabase apresenta um certificado emitido por uma CA **autoassinada** (`CN=Supabase Root 2021 CA`), que **não** está no bundle `/etc/ssl/certs/ca-certificates.crt` das imagens Linux. Por isso, `DB_SSLMODE=verify-full` falha com `SSL error: certificate verify failed` e o health check fica em `503`.

Configuração obrigatória:

1. Render > serviço `sosp-backend-staging` > **Environment** > **Secret Files** > **Add Secret File**.
2. **Filename:** `supabase-ca.crt`
3. **Contents:** conteúdo do certificado CA raiz do Supabase (`prod-ca-2021.crt`), obtido em Supabase > **Project Settings > Database > SSL Configuration > Download certificate**.
4. Salvar. O arquivo é montado em `/etc/secrets/supabase-ca.crt`, caminho já referenciado por `DB_SSLROOTCERT`.

> Este certificado é **público** (CA raiz), não é um segredo. Ainda assim, ele não é versionado no repositório: a montagem é feita pelo Secret File do Render.
> O código também detecta automaticamente `/etc/secrets/supabase-ca.crt` quando `DB_SSLROOTCERT` não está definido (`backend/config/settings/base.py`).

---

## 3. Configuração do Frontend na Cloudflare (Workers com OpenNext)

### 3.1 Modalidade Oficial: Cloudflare Workers Builds
A arquitetura do SOSP utiliza **Cloudflare Workers** acoplado ao adaptador oficial **`@opennextjs/cloudflare`**.
- **NÃO utilizar Cloudflare Pages estático:** O SOSP requer suporte a SSR/Edge Middleware, hidratação avançada do React 19 e rotas dinâmicas do App Router.
- **Configuração no Painel Cloudflare Workers & Pages:**
  1. Acesse o painel Cloudflare > **Compute (Workers) > Workers & Pages**.
  2. Clique em **Create application > Workers > Connect to Git** (Workers Builds).
  3. Selecione o repositório GitHub e a branch `develop`.
  4. Configure os parâmetros de build:
     - **Project Name:** `sosp-portal`
     - **Root directory:** `portal`
     - **Build command:** `npm run build:cloudflare` (executa `opennextjs-cloudflare build`)
     - **Deploy command:** `npx wrangler deploy` (ou automático via Workers Builds)
  5. O arquivo de configuração gerado no repositório é [`portal/wrangler.jsonc`](file:///Users/euoluizg/Desktop/CESMAC/EngenhariaDeSoftware/SOSP/portal/wrangler.jsonc):
     - `main`: `.open-next/worker.js` (código compilado do worker)
     - `assets`: `{"directory": ".open-next/assets", "binding": "ASSETS"}` (ativos estáticos servidos diretamente na CDN)
     - `compatibility_date`: `"2024-12-30"`
     - `compatibility_flags`: `["nodejs_compat"]`

### 3.2 Variáveis de Ambiente no Painel da Cloudflare

| Variável | Valor para Staging | Contexto | Descrição |
|---|---|:---:|---|
| `NEXT_PUBLIC_APP_ENV` | `staging` | Build & Runtime | Identificador do ambiente |
| `NEXT_PUBLIC_API_MOCK` | `false` | Build & Runtime | **Desativa mocks e conecta à API real** |
| `NEXT_PUBLIC_API_URL` | `https://sosp-backend-staging.onrender.com/api/v1` | Build & Runtime | URL base do backend no Render |
| `NEXT_PUBLIC_FEATURE_REVIEWS_ENABLED` | `false` | Build & Runtime | Feature flag v2.0 (desligada no MVP) |

> [!WARNING]
> NUNCA adicione segredos (`DB_PASSWORD`, `SECRET_KEY`, `DB_HMAC_SECRET_KEY`) no painel da Cloudflare. O frontend executa no navegador do cidadão e na borda Anycast, consumindo exclusivamente a API REST autenticada por tokens de sessão.

---

## 4. Política de Proteção e Isolamento do Banco de Dados

### 4.1 Ambiente Supabase Atual (Pré-Produção / Homologação Principal)
- O projeto Supabase atualmente provisionado (`aws-1-sa-east-1.pooler.supabase.com:5432`) possui o schema canônico 4C.2 e o modelo de segurança 4D.2 implantados e auditados.
- **Não executar testes destrutivos:** Jamais execute `DROP`, `TRUNCATE` ou deleções em lote nesse ambiente.

### 4.2 Opção de Segundo Projeto Supabase para Staging Descartável
- Caso o operador deseje um ambiente 100% isolado para testes com dados sintéticos volumosos:
  1. Criar novo projeto Supabase gratuito (`sosp-staging-ephemeral`).
  2. Aplicar o schema físico [`docs/database/schema.sql`](file:///Users/euoluizg/Desktop/CESMAC/EngenhariaDeSoftware/SOSP/docs/database/schema.sql).
  3. Aplicar os scripts de grants e RLS da 4D.2.
  4. Apontar o backend Render staging para esse novo host.

### 4.3 Auditoria de Menor Privilégio no Login (`authenticate_citizen_by_cpf`)
- A função [`scripts/security_audit/patch_least_privilege_auth_function.sql`](file:///Users/euoluizg/Desktop/CESMAC/EngenhariaDeSoftware/SOSP/scripts/security_audit/patch_least_privilege_auth_function.sql) opera sob `SECURITY DEFINER` com `SET search_path = pg_catalog, public, sosp_security`.
- **Mitigação de Exposição de Hashes:**
  - Validação estrita de regex: CPF deve ter exatamente 11 dígitos numéricos (`^[0-9]{11}$`).
  - Bloqueio temporal (`blockedUntil`): Se o usuário estiver bloqueado por força bruta, a função retorna `password_hash = NULL`, impossibilitando verificação.
  - Rate limiting no Django: Máximo de 5 tentativas inválidas consecutivas aciona lockout de 5 minutos (`RN-29`).
  - Permissão restrita: `REVOKE ALL ON FUNCTION ... FROM PUBLIC; GRANT EXECUTE ... TO sosp_runtime_role;`. O público externo não possui permissão de invocar a função SQL diretamente.

---

## 5. Runbook de Verificação Pós-Deploy (Smoke Tests)

1. **Health Check do Backend no Render:**
   ```bash
   curl -i https://sosp-backend-staging.onrender.com/api/v1/health
   # Resposta esperada: HTTP/1.1 200 OK com status "healthy"
   ```

2. **Consulta Pública de Serviços (Sem autenticação):**
   ```bash
   curl -i https://sosp-backend-staging.onrender.com/api/v1/services
   # Resposta esperada: HTTP/1.1 200 OK com array paginado de serviços
   ```

3. **Acesso ao Worker Cloudflare:**
   - Acessar `https://sosp-portal.workers.dev` (ou subdomínio atribuído pela Cloudflare) no navegador.
   - Inspecionar a aba Rede do DevTools:
     - Resposta do documento principal servida via Cloudflare Edge (`cf-ray` presente nos headers).
     - Chamadas para `/api/v1/...` direcionadas com sucesso ao Render sem erros de CORS (`access-control-allow-origin` presente).

---

## 6. Plano de Rollback e Contingência

### 6.1 Rollback no Render
1. Acesse o painel do Render > `sosp-backend-staging` > **Deploys**.
2. Identifique o deploy estável anterior.
3. Clique em **Rollback to this deploy**. O tráfego reverte imediatamente.

### 6.2 Rollback na Cloudflare Workers
1. Acesse o painel Cloudflare > **Compute (Workers) > sosp-portal > Deployments**.
2. Identifique a versão estável anterior na lista de versões.
3. Clique em **Rollback to this version**. A propagação na rede Anycast é instantânea (milissegundos).
