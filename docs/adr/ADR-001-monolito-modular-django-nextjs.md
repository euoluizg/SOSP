# ADR-001 — Monólito modular com Django e portal Next.js

- **Status:** Aceito
- **Data:** 29/10/2026
- **Decisores:** Arthur Franco e Luiz Gustavo — CESMAC
- **Substitui:** —
- **Substituído por:** —

## Contexto

O SOSP precisa entregar, em um semestre letivo, um ciclo completo de orientação, agendamento e acompanhamento para 14 requisitos funcionais. O time é pequeno e generalista, sem especialistas dedicados em infraestrutura distribuída. O domínio tem forte consistência transacional: um agendamento envolve cidadão, serviço, unidade, slot e protocolo na mesma operação; um protocolo não pode existir sem agendamento ou dúvida.

Ao mesmo tempo, o sistema tem duas audiências com necessidades opostas:

- **Cidadão:** interface pública, rápida, acessível, indexável e tolerante a conexão instável.
- **Servidor e administrador:** back-office denso, com CRUD, permissões, filtros e relatórios.

As alternativas consideradas foram: microsserviços, SPA React pura com API separada, serverless e um monólito tradicional sem fronteiras internas.

## Decisão

Adotamos um **monólito modular** com dois deployáveis:

1. **API Django 5 + DRF + Gunicorn**, organizada em nove módulos de domínio (`accounts`, `catalog`, `search`, `guidance`, `scheduling`, `feedback`, `notifications`, `reports`, `audit`), cada um com `models.py`, `selectors.py`, `services.py`, `serializers.py`, `views.py` e `tests/`.
2. **Portal Next.js 15 + React 19 + TypeScript**, com App Router, SSR/ISR e consumo exclusivo da API versionada.
3. **Back-office em Django Admin + HTMX**, sem reconstrução em React.
4. **Um banco PostgreSQL 17**, um Redis 7 e um object storage S3/MinIO.
5. **Contrato OpenAPI 3.0** como fronteira entre portal e API, com tipos TypeScript gerados do contrato.

As fronteiras entre módulos são verificadas no CI por um script que proíbe importar `models` de outro módulo. Cada módulo expõe serviços de aplicação e selectors; views nunca falam com models de outro módulo.

## Consequências positivas

| Consequência | Efeito |
|---|---|
| Uma transação ACID por caso de uso | Agendamento e protocolo nascem juntos ou não nascem |
| Um banco e um contrato | Menos superfície de falha e de integração |
| Django Admin pronto | Órgãos, unidades, serviços, usuários e relatórios com uma fração do esforço |
| Deploy independente de portal e API | Portal pode ser revertido sem reverter a API |
| Fronteiras explícitas | Um módulo pode virar serviço no futuro sem reescrever o domínio |
| Curva de aprendizado viável | Time generalista consegue operar Django e Next.js |

## Consequências negativas e trade-offs

| Trade-off | Custo aceito | Mitigação |
|---|---|---|
| Escala acoplada | A API escala como um todo, não por módulo | Réplicas horizontais e perfil de carga por rota |
| Um único banco | Um schema grande e migrações concorrentes | Prefixo por módulo, migrações expand/contract |
| Acoplamento acidental | Módulos podem importar models alheios | Script de fronteira no CI + revisão de PR |
| Dois deployáveis | Duas pipelines e dois conjuntos de logs | Pipeline unificado com jobs separados |
| Django Admin como back-office | UI menos customizável | HTMX para interações pontuais |
| SSR adiciona complexidade | Cache e invalidação precisam de cuidado | ISR com tags e cache Redis na API |

## Alternativas descartadas

### Microsserviços

Seria necessário service discovery, tracing distribuído, sagas para agendamento e consistência eventual para um domínio que é naturalmente transacional. O custo operacional é desproporcional ao time e ao volume inicial.

### SPA React pura com Vite

Perde SSR, prejudica SEO e primeira renderização, e obriga a duplicar autenticação e tratamento de sessão no cliente. O Next.js resolve esses pontos sem abrir mão da componentização.

### Serverless

Cold start na geração de PDF, limites de execução e estado distribuído tornam o modelo pior para o caso de uso. O custo seria imprevisível em picos de agendamento.

### Monólito tradicional sem módulos

É mais simples no primeiro mês e mais caro no sexto. Sem fronteiras, o domínio vira um conjunto de models e views acoplados, e qualquer extração futura exige reescrita.

## Critérios de verificação

| Critério | Como verificar |
|---|---|
| Nenhum módulo importa model de outro | `scripts/check_module_boundaries.py` no CI |
| Portal não acessa banco | Revisão de dependências e teste de contrato |
| API responde o contrato OpenAPI | `openapi-spec-validator` + testes de contrato |
| Back-office cobre CRUD dos módulos | Checklist de funcionalidades por módulo |
| Transações por caso de uso | Teste de integração com rollback forçado |

## Referências

- [Pilar 3 — Arquitetura de Software](../03-architecture.md)
- [Pilar 4 — Modelagem de Dados e Contratos de API](../04-data-api.md)
- Documento de Arquitetura SOSP, seções 3 e 4.
