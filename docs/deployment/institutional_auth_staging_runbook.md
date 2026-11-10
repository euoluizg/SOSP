# SOSP — Runbook supervisionado da autenticação institucional em staging

> **Ambiente:** Render (backend), Cloudflare Workers (portal) e Supabase PostgreSQL 17, projeto `cidtcgfowvgwgggvhbym`.
> **Responsáveis:** Tech Lead de Back-end/DevOps e operador autorizado.
> **Estado em 10/11/2026:** **RASCUNHO — NÃO EXECUTAR EM STAGING**. Falta ensaio da sequência e da recuperação em PostgreSQL 17 isolado, confirmação de backup restaurável e autorização humana específica.
> **Escopo:** somente autenticação de usuários institucionais. Não criar contas de cidadão ou dados fictícios de órgão/unidade.

## 1. Sequência e fontes canônicas

1. `backend/apps/accounts/migrations/0002_add_gender_description_and_unit_to_accounts.py` altera colunas, índice e constraints e registra o estado no `django_migrations`. Sua reversão é `RunPython.noop`; **não** usar `migrate accounts 0001_initial` como rollback físico.
2. `scripts/staging_ddl/04_apply_institutional_auth_and_schema_patch.sql` é a **única definição executável** da função institucional de 11 colunas. Ele exige a migration `accounts.0002` aplicada, configura `sosp_security` e concede `EXECUTE` a `sosp_runtime_role`. Não copiar uma segunda versão da função para o SQL Editor.
3. `sosp_runtime_app` herda `sosp_runtime_role` no projeto observado em 10/11/2026. Confirmar novamente a herança e o privilégio efetivo antes de cada execução.
4. `backend/render-build.sh` não executa migrations. A aplicação e a publicação são etapas distintas.

O patch SQL e a migration não devem modificar as mesmas colunas/constraints na mesma implantação. A ordem aprovada para ensaio é: **migration real → verificação física e do histórico → função SQL → verificação com a role de runtime → publicação → provisionamento**. Não usar `--fake`.

A `0002` combina mudanças aditivas (`genderDescription`, `unitId`, índice) e substituição de constraints. Os comandos `ALTER TABLE` podem bloquear escritas durante a aplicação; medir tamanho das tabelas, inspecionar locks e definir janela de execução antes de staging. O script da função faz `DROP/CREATE` dentro de uma transação, o que também exige teste de compatibilidade com a versão do backend em serviço.

**Evidência local em 10/11/2026:** em PostgreSQL 18.6 isolado, o Django aplicou `accounts.0001` e `accounts.0002`; o script institucional concluiu duas vezes; a função retornou 11 campos com `SECURITY DEFINER`, `search_path` fixo e `EXECUTE` apenas para `sosp_runtime_role`. Com uma linha sintética em transação revertida, a consulta direta como `sosp_runtime_app` retornou zero linhas sob RLS e a função encontrou a conta. Em outro banco isolado com somente `accounts.0001`, o script falhou na pré-condição e preservou a função de 10 campos. **Essa evidência não substitui o ensaio exigido em PostgreSQL 17.**

## 2. Estado conhecido e pré-voo somente leitura

O retrato de 10/11/2026 mostra `accounts.0001_initial` aplicado, `accounts.0002` pendente, `unitId` ausente em `accountsInternalUser`, ambas as funções de autenticação ausentes, zero usuários institucionais, zero cidadãos, zero unidades ativas e zero órgãos SSP ativos. A role `sosp_runtime_app` herda `sosp_runtime_role`; RLS está ativa nas tabelas de contas e sessões. **Este retrato não autoriza alterações e deve ser reconfirmado.**

Antes de qualquer operação, registrar em canal operacional privado: projeto e ambiente, branch e SHA do backend, revisão do PR #38, operador, janela, ponto de conexão, identidade administrativa, método de backup, procedimento de restauração e pessoa que decide interromper. Não registrar senha, hash, token, URL de conexão completa ou saída com dados pessoais.

Conectar por sessão direta ou *Session Pooler* na porta `5432`, conforme a opção **Connect** do projeto; confirmar host, usuário e projeto no gestor de segredos. A porta `6543` usa *Transaction Pooler* e não serve para este procedimento com estado de sessão ([modos de conexão do Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)). O Django lê `DB_ENGINE`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` e opções SSL de `backend/config/settings/base.py`; **`DATABASE_URL` isolada não configura essa conexão**. Definir as variáveis administrativas pelo gestor de segredos, sem colocá-las em comandos versionados ou histórico do shell. Exigir `DB_ENGINE=postgresql` e conferir o alias `default` antes de `showmigrations` ou `migrate`.

Consultas de pré-voo, sem conteúdo de usuários:

```sql
SELECT current_database(), current_user, current_setting('server_version_num') AS server_version;

SELECT app, name, applied FROM public.django_migrations
WHERE app = 'accounts' ORDER BY applied;

SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('accountscitizen', 'accountsinternaluser')
  AND column_name IN ('genderdescription', 'unitid', 'mustchangepassword')
ORDER BY table_name, column_name;

SELECT c.conrelid::regclass::text AS table_name, c.conname, pg_get_constraintdef(c.oid)
FROM pg_constraint c
WHERE c.conrelid IN ('public.accountsinternaluser'::regclass, 'public.accountssession'::regclass)
  AND c.contype = 'c'
ORDER BY table_name, c.conname;

SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) AS args,
       p.prosecdef AS security_definer, pg_get_userbyid(p.proowner) AS owner
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'sosp_security'
  AND p.proname IN ('authenticate_citizen_by_cpf', 'authenticate_internal_user_by_cpf');

SELECT pg_has_role('sosp_runtime_app', 'sosp_runtime_role', 'USAGE') AS runtime_inherits_role;

SELECT n.nspname, has_schema_privilege('sosp_runtime_app', n.oid, 'USAGE') AS runtime_schema_usage
FROM pg_namespace n WHERE n.nspname = 'sosp_security';

SELECT c.relname AS table_name, c.relrowsecurity AS rls_enabled,
       c.relforcerowsecurity AS rls_forced
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN ('accountscitizen', 'accountsinternaluser', 'accountssession');

SELECT pid, usename, state, wait_event_type, wait_event,
       age(clock_timestamp(), query_start) AS duration
FROM pg_stat_activity
WHERE wait_event_type = 'Lock' OR state = 'active';
```

Conferir também policies RLS, grants efetivos, contagens de contas/órgãos/unidades e linhas incompatíveis com as novas constraints. Não imprimir o texto de queries ativas; ele pode conter dados sensíveis. Se `sosp_security` não existir, a consulta de privilégio do schema retorna zero linhas; repetir após a criação.

## 3. Portões antes de staging

- [ ] PR #38 e SHA do artefato a publicar identificados; diff e testes revisados.
- [ ] Ensaio em PostgreSQL 17 **isolado**: aplicar `0001` real, executar `python manage.py migrate accounts 0002_add_gender_description_and_unit_to_accounts` com Django, executar o patch SQL, comparar schema e `django_migrations` antes/depois e testar função/RLS com a role efetiva. O teste de segurança existente que copia trechos de DDL não substitui esse ensaio da migration real.
- [ ] Verificar que a função de 11 colunas tem `SECURITY DEFINER`, `search_path` restrito, `PUBLIC` sem `EXECUTE`, `sosp_runtime_role` com `EXECUTE`, herança para `sosp_runtime_app` e acesso direto às contas bloqueado por RLS.
- [ ] Cobrir login institucional sem função de cidadão, assinatura legada de 10 colunas, ausência da função institucional, erro de permissão, troca obrigatória, revogação de sessão, token antigo/manipulado e servidor sem lotação.
- [ ] Confirmar backup **existente e restaurável**, ponto de recuperação, perda de dados admissível e ensaio de restauração em ambiente isolado. A organização Supabase foi consultada em 10/11/2026 e está no plano **Free**, que não oferece backup diário automático; preparar um dump lógico verificável antes da migration ([política de backups do Supabase](https://supabase.com/docs/guides/platform/backups)).
- [ ] Aprovação humana explícita para cada operação remota sensível: migration/SQL, provisionamento, alteração de credenciais, publicação, merge ou deploy.

**Parar** se conexão/role forem incertas, houver diferença não explicada no schema ou histórico, backup não verificável, função incompatível, grants/RLS inesperados, falha crítica no ensaio ou necessidade de dados fictícios.

## 4. Execução futura, somente após os portões e autorização

O operador deve usar um terminal administrativo temporário com as variáveis de `DB_*` carregadas pelo gestor de segredos. O processo não deve usar a identidade restrita do Render para DDL e não deve imprimir a configuração completa do banco.

```bash
cd backend
python manage.py showmigrations accounts
python manage.py migrate accounts 0002_add_gender_description_and_unit_to_accounts --plan
python manage.py migrate accounts 0002_add_gender_description_and_unit_to_accounts
```

Após a migration, confirmar que `accounts.0002_add_gender_description_and_unit_to_accounts` consta no histórico e que `genderDescription`, `unitId`, índice e constraints esperados existem. Interromper se histórico e schema não corresponderem. Para o `psql`, carregar `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` e SSL pelo gestor de segredos (as variáveis `DB_*` do Django não são lidas automaticamente pelo `psql`). Abrir uma conexão administrativa de sessão e confirmar o alvo **na mesma sessão**, antes de executar o patch canônico uma vez:

```bash
cd ..
psql -X -v ON_ERROR_STOP=1
```

```sql
SELECT current_database(), current_user, current_setting('server_version_num') AS server_version;
\i scripts/staging_ddl/04_apply_institutional_auth_and_schema_patch.sql
```

Os comandos acima pressupõem que o operador iniciou na **raiz do repositório** e recebeu a conexão administrativa de forma segura. Confirmar também o host/projeto pelo gestor de segredos; `current_database()` sozinho pode ser igual em projetos diferentes. Não preencher senha em argumento, URL ou variável exportada no histórico. Não usar o SQL Editor para colar uma segunda definição da função.

Verificar metadados da função e privilégios, incluindo `has_function_privilege('sosp_runtime_app', 'sosp_security.authenticate_internal_user_by_cpf(character varying)', 'EXECUTE')`. Testar invocação com a identidade de runtime em transação separada, sem registrar CPF, hash ou resposta bruta. Testar RLS com uma conta de ensaio no PostgreSQL isolado; no staging vazio, `count(*) = 0` sozinho **não prova** isolamento.

Somente depois dessas verificações, publicar backend e portal com os SHAs aprovados. O provisionamento das duas contas institucionais exige autorização separada. Usar `provision_homologation_users --interactive`; não usar flags de senha em argumentos. O comando exige duas senhas fornecidas por entrada sem eco ou gestor de segredos e não grava credenciais em arquivo. Sem SSP e unidade reais, `--allow-unlinked` permite apenas homologar autenticação: ações operacionais do servidor devem continuar bloqueadas. Não criar órgão/unidade fictícios nem conta de cidadão.

## 5. Homologação e recuperação

Homologar em navegador e API: login por CPF, resposta `mustChangePassword=true`, bloqueio dos endpoints protegidos antes da troca, troca de senha, revogação do token anterior, revalidação autoritativa do estado da conta, permissões por perfil, isolamento de órgão/unidade e bloqueio do servidor sem lotação. Registrar separadamente resultados de código, testes locais, PostgreSQL isolado, Supabase, Render, Cloudflare e navegador.

**Não executar** `migrate accounts 0001_initial` como recuperação: a reversão da `0002` é `noop` e o histórico ficaria incoerente. O script `04_rollback_institutional_auth_patch.sql` restaura uma função de dez colunas, mas a função estava ausente no staging de 10/11/2026; ele **não reproduz esse baseline** e não deve ser usado neste ambiente sem plano específico ensaiado. A alternativa de correção progressiva ou restauração precisa ser decidida conforme o ponto de falha e o backup verificado. Uma restauração completa pode perder escritas posteriores e exige aprovação própria.

Se a etapa falhar, parar novas publicações e provisionamento, preservar evidências sem segredos, identificar o último estado consistente e submeter o plano de correção/restauração ao responsável. Não remover colunas, constraints, tabelas ou registros de negócio de forma improvisada.
