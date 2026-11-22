---
name: postgresql-migration-safety
description: Planejamento de alterações seguras no schema PostgreSQL e migrations Django.
---

# Segurança de migrations

1. Leia models, migrations e dependências atuais.
2. Classifique mudanças como aditivas, transformações ou destrutivas.
3. Analise locks, tamanho de tabelas, índices e compatibilidade entre versões.
4. Para mudanças arriscadas, proponha estratégia expand/contract, backup e rollback.
5. Apresente SQL ou migration para revisão antes de aplicar em ambientes compartilhados.
6. Nunca execute operações destrutivas sem aprovação explícita.
