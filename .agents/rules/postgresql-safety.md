---
trigger: always_on
description: Segurança operacional para PostgreSQL e migrations Django: proibição de operações destrutivas sem aprovação.
---

# Segurança PostgreSQL e migrations

Antes de migrations, analise schema, dependências, locks, reversibilidade e impacto em dados. Nunca rode DROP, TRUNCATE, flush, migrations de produção ou operações irreversíveis sem autorização explícita. Não use --fake nem apague histórico de migrations sem aprovação.
