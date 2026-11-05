---
name: django-backend-workflow
description: Fluxo de planejamento, implementação e verificação de funcionalidades Django e APIs REST.
---

# Fluxo de desenvolvimento Django

1. Inspecione versões, apps, settings, urls, modelos e testes existentes.
2. Defina contrato de API: rota, método, autenticação, payload, resposta e erros.
3. Identifique impacto no schema e peça aprovação antes de mudanças sensíveis.
4. Implemente de forma incremental e com testes para casos positivos, negativos e permissões.
5. Execute verificações disponíveis, por exemplo `python manage.py check` e testes adequados, apenas após conferir ambiente e dependências.
6. Entregue resumo, arquivos, migrations, evidências de testes e riscos.
