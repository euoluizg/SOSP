---
trigger: always_on
description: Execução segura e não destrutiva dos testes.
---

- Somente leitura até aprovação.
- Produção proibida por padrão.
- Não executar reset, truncate, delete, migration ou seed destrutivo sem autorização.
- Carga somente em ambiente autorizado.
- Pare diante de risco operacional.
