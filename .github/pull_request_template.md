## Resumo da Entrega

- **Task / Card:** `[FE | BE] [RFXXX] <Título da Task> (<Prioridade>)`
- **Requisito Funcional (`RF`):** `RF-XX`
- **Caso de Uso (`UC`):** `UC-XX`
- **Telas no Figma (`01`–`30` / `W01`–`W15`):** `—`
- **Critérios de Aceite atendidos (`CA`):** `CA-XX`

### O que foi feito?
- 

---

## Checklist de Revisão (Definition of Done — Pilar 5 §3.3)

### Geral e Arquitetura
- [ ] **1. Rastreabilidade:** PR vinculado ao `RF`, `UC`, `CA` e branch nomeada no padrão `feat/<fe|be>/rfxxx-<slug>` (`ADR-004`).
- [ ] **2. Hierarquia e Divergências:** Implementação segue o requisito e resolve eventuais divergências mapeadas em `D1–D13` (`Pilar 1 §7`).
- [ ] **3. Contrato Sincronizado:** Qualquer mudança de rota/payload ou tabela foi refletida em `docs/api/openapi.yaml` e `docs/database/schema.sql`.
- [ ] **4. Feature Flags (`ADR-007`):** Se tocar em `RF-10` ou `RF-13`, está protegido pela respectiva flag desligada por padrão no MVP.

### Back-end (`Django 5 + DRF`) — *Marcar N/A se for apenas `[FE]`*
- [ ] **5. Monólito Modular (`ADR-001`):** Zero importação direta de `models.py` entre módulos diferentes (comunicação via `services.py` / `selectors.py`).
- [ ] **6. PostgreSQL `camelCase` (`ADR-002`):** `db_table` e `db_column` idênticos ao `schema.sql`.
- [ ] **7. Segurança, Exclusão Lógica e Auditoria (`RS-01..05`):** Permissões RBAC aplicadas, sem `DELETE` físico (`isActive=False` / `deletedAt`) e log gravado em `auditEvent`.
- [ ] **8. Erros `RFC 7807`:** Exceções retornam `application/problem+json` com as mensagens literais em português do requisito.

### Front-end (`Next.js 15`) — *Marcar N/A se for apenas `[BE]`*
- [ ] **9. Consumo via API REST:** Zero acesso direto ao banco/Supabase; tipagem TypeScript estrita sem `any`.
- [ ] **10. Quatro Estados de Interface (`Pilar 2 §4`):** Estados `loading`, `empty`, `error` e `success` implementados.
- [ ] **11. Responsividade e Design System:** Tokens `.sosp-` aplicados e layout validado em `390 px` (Mobile) e `1440 px` (Desktop).
- [ ] **12. Acessibilidade (`WCAG 2.1 AA`):** Navegação por teclado, `<label>` em todos os campos, foco visível e zero erros críticos no `axe-core`.

### Qualidade e CI
- [ ] **13. Testes Automatizados:** Testes unitários/integração passando (`pytest` / `vitest` / `playwright`) mantendo a meta de cobertura (`≥ 80%` BE / `≥ 70%` FE).
- [ ] **14. Demo e Documentação:** Fluxo da `docs/demo-7-minutos.md` preservado e `CHANGELOG.md` atualizado se necessário.

---

## Evidências (Screenshots / Logs de Teste)

<!-- Cole abaixo prints das telas (Mobile 390px / Desktop 1440px) ou saída dos testes -->

