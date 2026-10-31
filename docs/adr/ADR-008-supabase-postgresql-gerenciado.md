# ADR-008 — Supabase como PostgreSQL gerenciado (e não como Backend-as-a-Service)

- **Status:** Aceito
- **Data:** 31/10/2026
- **Decisores:** Equipe de Engenharia de Software — CESMAC
- **Substitui:** —
- **Substituído por:** —

## Contexto

O SOSP precisa de um PostgreSQL operado com backup, TLS, atualização de versão e conexão de baixa latência a partir do Brasil. O time é pequeno e não tem plantão de banco: alguém precisa garantir que o dado esteja disponível na demonstração e que o restore funcione.

Três caminhos foram considerados:

1. **PostgreSQL auto-hospedado** em uma VM — controle total, mas backup, patch, monitoramento e failover viram responsabilidade do time.
2. **PostgreSQL gerenciado puro** (RDS, Cloud SQL, Neon) — resolve a operação, mas exige conta, cartão e configuração de rede.
3. **Supabase** — oferece PostgreSQL gerenciado, mas também Auth, Data API (PostgREST), Realtime e Storage. Usar o Supabase inteiro criaria uma segunda porta de escrita e duplicaria responsabilidades com o Django.

A região disponível em São Paulo (`sa-east-1`) atende à latência e à expectativa de residência de dados. O Supabase oferece PostgreSQL 17 no plano usado pelo projeto.

O risco principal não é técnico, é de **arquitetura acidental**: alguém começa a usar a Data API porque "é mais rápido", o portal passa a falar direto com o banco e as regras de negócio se dividem entre Django e PostgREST. O projeto precisa de uma decisão explícita que limite o Supabase ao papel de banco.

## Decisão

### Supabase é somente PostgreSQL gerenciado

| Recurso do Supabase | Uso no SOSP | Justificativa |
|---|---|---|
| **PostgreSQL** | **Sim** | Fonte única de verdade, na versão 17, região `sa-east-1` |
| **Auth** | Não | Identidade é do Gov.br (cidadão) e do Django (servidor), conforme ADR-003 |
| **Data API (PostgREST)** | Não | O Django é a única porta de escrita e a única API pública |
| **Realtime** | Não | Não há requisito de atualização push de dados no MVP |
| **Storage** | Opcional | Pode substituir S3/MinIO por ser compatível com a API S3; ver ADR-006 |
| **Edge Functions** | Não | Regra de negócio vive no Django; função de borda criaria duplicidade |
| **Supavisor (pooler)** | Sim | Conexão da aplicação em ambiente serverless/gerenciado |

**Regra de ouro:** o portal e qualquer cliente externo **nunca** falam com o banco. Toda leitura e escrita passa pela API Django, que aplica RBAC, validação, auditoria e regra de negócio.

### Versão e schema

- **PostgreSQL 17** em todos os ambientes. O Docker local usa a mesma major version; a divergência de versão entre dev e produção é proibida.
- Schema da aplicação em **`public`**. As extensões `pg_trgm` e `unaccent` também ficam em `public`, porque o DDL atual as referencia sem schema qualificado.
- `uuidv7()` **não** é usado: a função é nativa no PostgreSQL 18. O default permanece `gen_random_uuid()` (v4); a migração para v7 está registrada no ADR-002.
- O schema é criado por `docs/database/schema.sql` e evoluído por migrações do Django. O Supabase não é usado para editar schema à mão.

### Conexão

| Uso | Conexão | Configuração |
|---|---|---|
| Aplicação (API e workers) | **Session pooler** (Supavisor, porta 5432) | `DATABASE_URL`, `sslmode=require` |
| Migrações, `pg_dump`, scripts | **Conexão direta** (porta 5432) | `DATABASE_DIRECT_URL` |
| Transaction pooler (porta 6543) | Não recomendado para o Django | Exigiria `DATABASE_DISABLE_SERVER_SIDE_CURSORS=true` e `DATABASE_CONN_MAX_AGE=0` |

**Por que Session pooler:** o Django usa cursores nomeados e prepared statements; o Transaction pooler não preserva estado de sessão entre transações. O Session pooler mantém a sessão e evita o erro clássico de `server-side cursors`. Se o Transaction pooler for necessário por limite de conexões, as duas variáveis acima passam a ser obrigatórias.

`DATABASE_CONN_MAX_AGE=60` no Session pooler; `0` no Transaction pooler. O `statement_timeout` é de 5 s (`DATABASE_STATEMENT_TIMEOUT_MS`).

### Segurança

1. **`service_role` nunca no portal, no repositório ou em `NEXT_PUBLIC_*`.** A chave ignora RLS e dá acesso total ao banco. Ela não é usada pela aplicação: o Django conecta com o usuário do banco, não com a chave de serviço.
2. **Data API desabilitada.** Sem PostgREST exposto, não há endpoint público do Supabase para o portal.
3. **RLS como defesa em profundidade.** As tabelas com dado pessoal têm RLS habilitado e políticas que negam acesso anônimo. Como o Django usa o usuário owner, a RLS não é o mecanismo principal de autorização — é a segunda barreira caso a Data API seja ligada por engano.
4. **Rede:** conexão TLS obrigatória; IP allowlist quando o plano permitir; acesso direto restrito a migrações.
5. **Segredos:** `DATABASE_URL`, `DATABASE_DIRECT_URL` e credenciais de storage vêm do secret manager do ambiente. O `.env` local usa o PostgreSQL do Docker, nunca a credencial de produção.
6. **Auditoria:** o Supabase não substitui o `auditEvent` da aplicação. Toda ação sensível é registrada pelo Django.

### Backup e continuidade

| Item | Decisão |
|---|---|
| Backup automático | Diário, retenção conforme o plano; verificar o horário |
| PITR | Habilitar se o plano oferecer; documentar a janela |
| Backup lógico adicional | `pg_dump` semanal via `DATABASE_DIRECT_URL`, guardado fora do Supabase |
| Restore | Ensaio trimestral em banco separado; registrar data e resultado no Pilar 5 §8 |
| RPO/RTO | RPO ≤ 24 h (backup diário); RTO ≤ 4 h (restore documentado) |
| Exportação final | Antes da apresentação, dump completo guardado no repositório de evidências |

**Regra:** o Supabase é o provedor, não a estratégia de backup. Um dump fora do provedor é obrigatório para não depender de uma única conta.

### Limites e o que não fazer

| Não fazer | Por quê |
|---|---|
| Usar `supabase-js` no portal | Cria segunda porta de escrita e ignora o Django |
| Criar tabela pelo painel do Supabase | Foge do versionamento e do `schema.sql` |
| Guardar `service_role` em variável `NEXT_PUBLIC_*` | A chave fica visível no navegador |
| Usar Auth do Supabase para o cidadão | Contradiz o ADR-003 (Gov.br) |
| Confiar na RLS como autorização principal | A autorização é do Django; RLS é defesa em profundidade |
| Habilitar Realtime para "atualizar a tela" | Não há requisito; adiciona conexão persistente e custo |
| Editar dado em produção pelo SQL Editor | Sem auditoria, sem validação, sem migração |

## Consequências positivas

| Consequência | Efeito |
|---|---|
| Banco operado | Backup, patch e TLS deixam de ser tarefa do time |
| Região São Paulo | Latência menor e residência de dados no Brasil |
| PostgreSQL 17 | Versão atual, compatível com o Docker local |
| Uma porta de escrita | Regra de negócio, RBAC e auditoria concentrados no Django |
| Storage opcional | Menos um provedor se o Supabase Storage for adotado |
| Pooler documentado | Evita o erro de cursor e o esgotamento de conexões |

## Consequências negativas e trade-offs

| Trade-off | Custo aceito | Mitigação |
|---|---|---|
| Dependência de provedor | Migração exige dump/restore | PostgreSQL padrão + dump semanal fora do provedor |
| Plano gratuito tem limites | Conexões, backup e PITR restritos | Monitorar conexões; upgrade antes da apresentação |
| RLS mal configurada dá falsa segurança | Data API desabilitada reduz o risco | Revisão de políticas + teste de acesso anônimo |
| Pooler adiciona latência | Uma camada a mais | Session pooler e conexão direta para migrações |
| Duas URLs de conexão | Confusão entre app e migração | `DATABASE_URL` x `DATABASE_DIRECT_URL` documentadas no `.env.example` |
| Região única | Sem failover multi-região | Aceito no contexto acadêmico; RTO documentado |

## Alternativas descartadas

### Supabase completo (Auth + Data API + Realtime + Storage)

Seria rápido para um protótipo, mas criaria duas fontes de verdade: o Django e o PostgREST. Regras como "só o próprio cidadão vê o protocolo" teriam de ser replicadas em RLS e em Django, com risco de divergência. O projeto perderia a auditoria centralizada e a validação de negócio.

### PostgreSQL auto-hospedado em VM

Daria controle total e nenhum custo de serviço gerenciado, mas transferiria backup, patch, monitoramento e failover para um time sem plantão. O risco de perder a demonstração por disco cheio ou versão desatualizada é maior que o custo do serviço gerenciado.

### Amazon RDS ou Cloud SQL

São opções maduras, mas exigem conta de nuvem, configuração de VPC e um processo de provisionamento que o time não tem. O Supabase reduz o atrito e já entrega a região de São Paulo.

### Neon ou outro PostgreSQL serverless

Atende ao requisito de banco gerenciado, mas o modelo de branching e o cold start não foram validados para o padrão de conexão do Django. O Supabase foi escolhido por já estar disponível para o time e por oferecer o pooler documentado.

### SQLite no MVP

Simplificaria o desenvolvimento, mas não suporta full-text em português com `unaccent`, `pg_trgm`, concorrência de escrita e o schema real. O MVP precisa de PostgreSQL desde o primeiro dia para não trocar o banco na véspera.

## Critérios de verificação

| Critério | Como verificar |
|---|---|
| Versão do banco é 17 | `SHOW server_version;` em staging e produção |
| Schema em `public` | `SELECT table_schema FROM information_schema.tables` |
| Data API desabilitada | Painel do Supabase + requisição anônima deve falhar |
| Auth do Supabase desabilitado | Nenhum usuário no painel de Auth; login só pelo Django/Gov.br |
| `service_role` ausente do repositório | Varredura por `service_role` e `SUPABASE_SERVICE_ROLE_KEY` |
| Portal não acessa o banco | Nenhuma dependência `@supabase/*` em `portal/package.json` |
| Pooler funciona | Teste de conexão e execução de query pela API |
| Migração usa conexão direta | Log de `migrate` aponta para `DATABASE_DIRECT_URL` |
| Restore testado | Ensaio documentado no Pilar 5 §8 |

## Referências

- [Pilar 3 — Arquitetura](../03-architecture.md)
- [Pilar 4 — Modelagem de Dados e Contratos de API](../04-data-api.md)
- [Pilar 5 — Engenharia, DevOps e Operação](../05-engineering-devops.md)
- [ADR-002 — PostgreSQL e convenção `camelCase`](ADR-002-postgresql-camelcase.md)
- [ADR-003 — Autenticação Gov.br e RBAC](ADR-003-autenticacao-govbr-rbac.md)
- [ADR-006 — Armazenamento S3/MinIO](ADR-006-armazenamento-s3-minio.md)
- [`.env.example`](../../.env.example)
