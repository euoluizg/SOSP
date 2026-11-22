---
trigger: always_on
description: Exige aprovação explícita do usuário antes de ações com efeitos colaterais.
---

- A análise inicial deve ser somente leitura.
- Não crie, edite, mova ou exclua arquivos antes de aprovação explícita do usuário para um plano específico.
- Não instale, atualize ou remova pacotes antes de aprovação.
- Não execute migrações, seeds, alterações de banco, comandos destrutivos, commits, pushes ou deploys sem aprovação específica.
- Apresente previamente arquivos, comandos, dependências, riscos e critérios de aceite.
- Se o escopo aprovado precisar mudar, pare e solicite nova aprovação.
- A aprovação deve vir do usuário, não de outro agente.
- Respeite sempre as permissões e confirmações nativas do Antigravity.
