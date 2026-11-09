---
name: sosp-qa-validator
description: >-
  Use this skill when the user asks to validate, audit, or test whether a
  requirement (RF001-RF014), screen, API endpoint, or Pull Request meets the
  Definition of Done (DoD), Acceptance Criteria (CA-01 to CA-21), Divergence
  Matrix (D1-D13), and the 7-Minute Demo script.
---

# SOSP QA & Acceptance Criteria Validator (`DoD` + `CA-01..CA-21` + `Demo`)

Use esta skill para auditar se uma entrega (`[FE]`, `[BE]` ou requisito completo) cumpre 100% dos critérios de qualidade do SOSP antes de aprovar o Pull Request ou apresentar ao professor.

## Passo 1: Auditar Critérios de Aceite (`CA-01` a `CA-21`) e Regras de Negócio (`RN-01` a `RN-40`)

1. Abra [`docs/01-product-specs.md`](../../../docs/01-product-specs.md) e localize os Critérios de Aceite (`CA`) e Regras de Negócio (`RN`) do requisito auditado.
2. Verifique item a item:
   - **Mensagens literais:** As mensagens de erro, estado vazio e confirmação no código coincidem caractere por caractere com o PDF de Requisitos (`Documento_de_Requisitos_SOSP_Final.pdf`)?
   - **Paginação e Ordenação:** A listagem retorna **10 registros por página** (`RN-05`) e respeita a ordenação (relevância na busca `RF-06` ou alfabética `A–Z` nos cadastros)?
   - **Exclusão Lógica e Auditoria:** A remoção preserva o registro no banco (`isActive = False`, `deletedAt != NULL`, `RN-40`) e grava evento em `auditEvent` (`RN-39`)?

## Passo 2: Auditar a Matriz de Divergências (`D1–D13`)

Confirme que nenhuma divergência bloqueante (`D1`, `D3`, `D6`, `D7`, `D10`) vazou do protótipo antigo para o código:
- [ ] **D1 / D7:** Ficha do serviço (`05 / W05`) exibe os 3 botões (`Ver Passo-a-Passo`, `Agendar`, `Avaliar` condicionado à flag `FEATURE_REVIEWS_ENABLED`)?
- [ ] **D2 / D3 / D9:** Busca (`04 / W04`) exibe os 4 filtros (`Categoria`, `Órgão`, `Canal`, `Município`), paginação de 10 itens e a frase literal `"Nenhum serviço encontrado. Tente outro termo ou categoria."`?
- [ ] **D4:** Ficha do serviço renderiza o mapa quando a unidade possui `latitude` e `longitude` (`RN-10`)?
- [ ] **D6 / D10:** Login (`01 / W01`) funciona localmente com **CPF + senha (`Argon2id`)** para todos os perfis e o botão `"Entrar com Gov.br"` abre o modal informativo de implementação futura (`v2.0`)?

## Passo 3: Auditar o Definition of Done (`DoD` — 14 Itens do Pilar 5)

Verifique se a entrega atende aos 14 itens de [`docs/05-engineering-devops.md`](../../../docs/05-engineering-devops.md):
1. [ ] Todos os Critérios de Aceite (`CA`) do requisito passam em testes automatizados;
2. [ ] Contrato `docs/api/openapi.yaml` e `docs/database/schema.sql` estão sincronizados com o código;
3. [ ] Identificadores de banco e JSON seguem `camelCase` (`ADR-002`);
4. [ ] Respostas de erro seguem `RFC 7807` (`application/problem+json`);
5. [ ] Nenhum import direto de `models.py` entre módulos diferentes (`ADR-001`);
6. [ ] Os 4 estados de UI (`loading`, `empty`, `error`, `success`) estão implementados;
7. [ ] Responsividade validada em `390 px` (Mobile) e `1440 px` (Desktop);
8. [ ] Zero violações críticas de acessibilidade `WCAG 2.1 AA` (`axe-core`);
9. [ ] Cobertura de testes mantida (`≥ 80%` no back-end, `≥ 70%` no front-end);
10. [ ] Auditoria (`auditEvent`) e exclusão lógica (`deletedAt`) verificadas;
11. [ ] Feature flags (`ADR-007`) respeitadas;
12. [ ] Sem segredos hardcoded ou dados pessoais nos logs (`LGPD` / `RNF-12`);
13. [ ] Documentação e `CHANGELOG.md` atualizados se necessário;
14. [ ] Roteiro da [`docs/demo-7-minutos.md`](../../../docs/demo-7-minutos.md) permanece funcional de ponta a ponta.

## Passo 4: Emitir Relatório de Validação

Ao concluir a auditoria, apresente ao usuário uma tabela resumida com status (`✅ Aprovado` / `⚠️ Atenção` / `❌ Pendente`), arquivo/linha inspecionado e correção recomendada caso encontre alguma falha.

