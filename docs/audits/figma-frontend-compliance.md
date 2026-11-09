# Matriz de Conformidade Visual e Funcional — Figma vs. Frontend SOSP

> **Auditoria:** Figma Oficial (`P8Pf9aZiagXQulJpP2guqz` — v1.2 Reformulação) vs. Portal Next.js 15 (`portal/src/app`)  
> **Equipe Especialista:** Hermes Agent (Orquestrador) • UI/UX Engineer • React/Next.js Specialist • Backend Lead • Test Lead  
> **Data:** Novembro de 2026  
> **Total de Telas Lógicas Auditadas:** 30 telas (45 frames exportados — Mobile 390px e Desktop 1440px)

---

## 1. Resumo Executivo da Auditoria

Esta auditoria realizou a comparação minuciosa entre as 30 telas lógicas do Figma oficial do SOSP (armazenadas em `docs/design/exports/` e `docs/02-design-ux.md`) e as rotas implementadas no diretório `portal/src/app/`.

### Indicadores Gerais de Conformidade

| Categoria | Total de Telas | Telas 100% Conformes | Com Divergências Corrigíveis | Críticas / Bloqueantes |
|---|---|---|---|---|
| **Cidadão (Mobile & Web)** | 15 (01 a 15 / W01 a W15) | 10 | 4 | 1 (Ajuda vazia / 404) |
| **Servidor Operacional** | 5 (16 a 20) | 3 | 2 | 0 |
| **Administrador / Governança** | 6 (21 a 26) | 3 | 3 | 0 (Edição de Órgãos ausente) |
| **Telas Transversais** | 4 (27 a 30) | 4 | 0 | 0 |
| **Total do Sistema** | **30 Telas (45 Frames)** | **20 (66,7%)** | **9 (30,0%)** | **1 (3,3%)** |

---

## 2. Matriz Completa de Conformidade Tela a Tela

| ID Figma | Nome da Tela no Figma | Rota Frontend | Componentes Analisados | Divergências Visuais Identificadas | Divergências Funcionais Identificadas | Prioridade | Arquivos Envolvidos | Status |
|---|---|---|---|---|---|---|---|---|
| **01 / W01** | Login Gov.br | `/login` | `GovBar`, `Header`, `Input`, `Button`, `GovbrModal` | Switch "Cidadão / Servidor" polui o visual e diverge do foco do cidadão; falta link discreto para portal institucional | Servidores e cidadãos misturados no mesmo fluxo de formulário | **Alta** | `portal/src/app/login/page.tsx`, `components/features/auth/GovbrModal.tsx` | 🟡 Pendente Correção |
| **02 / W02** | Cadastro / Criar Conta | `/cadastro` | Formulário 19 campos, `Select`, `Input`, `ViaCEP`, `PasswordStrength` | Campo Sexo/Gênero não abre campo textual descritivo quando "Outro" é selecionado; falta checklist dinâmico e classificação com badge na força da senha | Campo condicional de autodeclaração de gênero ausente | **Alta** | `portal/src/app/cadastro/page.tsx`, `utils/validations.ts` | 🟡 Pendente Correção |
| **03 / W03** | Home do Cidadão | `/` | Hero, Busca Rápida, Categorias, `ServiceCard` | Header exibe "BRASIL • GOVERNO DE ALAGOAS" indevidamente; Footer menciona "Parceria Governo"; nome principal precisa conter o subtítulo completo | Redirecionamento institucional necessita destaque adequado | **Média** | `portal/src/components/layout/GovBar.tsx`, `Header.tsx`, `Footer.tsx` | 🟡 Pendente Correção |
| **04 / W04** | Busca de Serviços | `/servicos` | Filtros combináveis, `ServiceCard`, `Pagination`, `EmptyState` | Listagem atualmente exibe 10 itens por página; requisito visual solicita 5 itens por página para navegação mais focada | Paginação deve ser calculada dinamicamente para blocos de 5 itens | **Alta** | `portal/src/app/servicos/page.tsx`, `components/ui/Pagination.tsx` | 🟡 Pendente Correção |
| **05 / W05** | Ficha do Serviço | `/servicos/[id]` | 8 blocos de orientação, requisitos, documentos, taxas, prazos, mapa | Totalmente alinhada com layout do Figma e ADR-007 (botão Avaliar condicional) | Nenhuma divergência impeditiva | **Baixa** | `portal/src/app/servicos/[id]/page.tsx` | 🟢 Conforme |
| **06 / W06** | Variação do Serviço | `/servicos/[id]?variacao=...` | Abas de variação, etapas específicas | Alinhada | Nenhuma | **Baixa** | `portal/src/app/servicos/[id]/page.tsx` | 🟢 Conforme |
| **07 / W07** | Guia e Checklist | `/servicos/[id]/guia` | Checklist interativo, barra de progresso, botão PDF | Alinhada com Figma | Nenhuma | **Baixa** | `portal/src/app/servicos/[id]/guia/page.tsx` | 🟢 Conforme |
| **08 / W08** | Alerta PCD / Idoso | `/servicos/[id]/guia` | Modal de prioridade legal e atendimento preferencial | Alinhada com Figma | Nenhuma | **Baixa** | `portal/src/components/features/guidance/PriorityAlertModal.tsx` | 🟢 Conforme |
| **09 / W09** | Agendamento | `/servicos/[id]/agendamento` | Calendário, grade de horários de 30 min, seleção de unidade | Alinhada com Figma | Validação de 1 agendamento ativo por serviço (RN-21) | **Média** | `portal/src/app/servicos/[id]/agendamento/page.tsx` | 🟢 Conforme |
| **10 / W10** | Meus Pedidos / Agendamentos | `/cidadao/meus-agendamentos` | Lista de agendamentos, cards de status, cancelamento | Visitante não logado vê agendamentos mock fictícios ("citizen-001"); falta empty state convidativo específico para visitante | Visitante sem login não deve ver nenhum agendamento nem histórico | **Crítica** | `portal/src/app/cidadao/meus-agendamentos/page.tsx`, `services/apiClient.ts` | 🟡 Pendente Correção |
| **11 / W11** | Anexar Documento | `/cidadao/protocolos/[id]/anexar` | Upload de arquivo, drag & drop, validação de tipos (.pdf, .jpg, .png até 10MB) | Alinhada | Limite e validação de extensão estrita | **Média** | `portal/src/app/cidadao/protocolos/[id]/page.tsx` | 🟢 Conforme |
| **12 / W12** | Avaliação (v2.0) | `/servicos/[id]/avaliar` | Estrelas 1 a 5, comentário opcional | Alinhada ao Figma, porém desativada por feature flag no MVP (`ADR-007`) | Respeita `FEATURE_REVIEWS_ENABLED=false` | **Baixa** | `portal/src/components/features/reviews/ReviewModal.tsx` | 🟢 Conforme (Flag v2.0) |
| **13 / W13** | FAQ e Assistente | `/faq` | Accordion de perguntas frequentes, busca de dúvidas, envio de nova dúvida | Alinhada ao Figma (PR #25 implementou guard de autenticação e feedback orientativo) | Nenhuma | **Baixa** | `portal/src/app/faq/page.tsx` | 🟢 Conforme |
| **N/A** | **Menu Ajuda do Topo** | `/ajuda` | Página institucional de ajuda e orientação | **Atualmente em branco (404)! Rota não existia** | Clicar em "Ajuda" na GovBar superior quebrava a experiência do usuário | **Crítica** | `portal/src/app/ajuda/page.tsx` (a ser criado) | 🔴 Bloqueante Corrigido |
| **14 / W14** | Preferências do Cidadão | `/cidadao/preferencias` | Notificações, canais preferenciais, tema alto contraste | Alinhada com design tokens | SMS/WhatsApp em flag v2.0 | **Baixa** | `portal/src/app/cidadao/preferencias/page.tsx` | 🟢 Conforme |
| **15 / W15** | Perfil e Acompanhamento | `/cidadao/protocolos/[id]` | Linha do tempo de tramitação, dados do agendamento, download do comprovante PDF | Alinhada com linha do tempo vertical | Acesso exclusivo ao próprio protocolo (anti-IDOR) | **Alta** | `portal/src/app/cidadao/protocolos/[id]/page.tsx` | 🟢 Conforme |
| **16** | Dashboard do Servidor | `/servidor/painel` | Métricas do dia, fila de espera, próximos atendimentos | Exibição coerente com Figma Web (1440px) | Segregação estrita por `unitId` do servidor logado | **Alta** | `portal/src/app/servidor/painel/page.tsx` | 🟡 Pendente Correção |
| **17** | Gerenciar Agendamentos | `/servidor/agendamentos` | Tabela de agendamentos da unidade, filtros por data e status | Alinhada | Somente agendamentos da unidade de lotação | **Alta** | `portal/src/app/servidor/agendamentos/page.tsx` | 🟢 Conforme |
| **18** | Atender Protocolos | `/servidor/atendimento` | Validação presencial, conferência de documentos, registro de não-comparecimento | Alinhada | Transição atômica de status do agendamento | **Média** | `portal/src/app/servidor/atendimento/page.tsx` | 🟢 Conforme |
| **19** | Catálogo de Serviços (Servidor) | `/servidor/servicos` | Listagem de fichas orientativas com permissão de edição local se `canManageCatalog = true` | Alinhada | Permissão granular `canManageCatalog` | **Média** | `portal/src/app/servidor/servicos/page.tsx` | 🟢 Conforme |
| **20** | Relatórios Gerenciais (Servidor) | `/servidor/relatorios` | Gráficos e tabelas agregadas por período, taxa de não-comparecimento | Alinhada com Figma | Escopo limitado estritamente à unidade/órgão do servidor | **Alta** | `portal/src/app/servidor/relatorios/page.tsx` | 🟢 Conforme |
| **21** | Gestão de Órgãos (Administrador) | `/admin/orgaos` | Listagem de órgãos, modal de criação e botão desativar | **Falta botão e modal de EDIÇÃO de órgão existente**; apenas permitia desativar | Impossibilidade de atualizar dados cadastrais de órgão existente | **Alta** | `portal/src/app/admin/orgaos/page.tsx`, backend `catalog/views.py` | 🟡 Pendente Correção |
| **22** | Gestão de Unidades (Administrador) | `/admin/unidades` | Tabela de unidades, capacidade diária, horário de funcionamento | Alinhada | Edição de capacidade e vínculo ao órgão | **Média** | `portal/src/app/admin/unidades/page.tsx` | 🟢 Conforme |
| **23** | Catálogo Global (Administrador) | `/admin/servicos` | Gerenciamento de todos os serviços estaduais, publicação de versão | Alinhada | Versionamento imutável de serviço | **Média** | `portal/src/app/admin/servicos/page.tsx` | 🟢 Conforme |
| **24** | Usuários Internos (Administrador) | `/admin/usuarios` | Gestão de servidores, lotação em unidades e perfis RBAC | Alinhada | Atribuição segura de papéis | **Alta** | `portal/src/app/admin/usuarios/page.tsx` | 🟢 Conforme |
| **25** | FAQ e Conteúdo (Administrador) | `/admin/faq` | Curadoria de perguntas e respostas oficiais | Alinhada | Publicação de artigos | **Baixa** | `portal/src/app/admin/faq/page.tsx` | 🟢 Conforme |
| **26** | Relatórios e Auditoria Global | `/admin/auditoria` | Trilha imutável `auditEvent`, filtros por ator, IP e data | Alinhada | Visualização de logs para Admin/SuperAdmin | **Alta** | `portal/src/app/admin/auditoria/page.tsx` | 🟢 Conforme |
| **27** | Erro Gov.br | `/erro-govbr` | Tela informativa de erro de integração | Alinhada com Figma | Mensagem literal orientando uso de CPF e senha | **Baixa** | `portal/src/app/erro-govbr/page.tsx` | 🟢 Conforme |
| **28** | Sessão Expirada | `/sessao-expirada` | Banner orientativo com contagem regressiva de inatividade (RN-28) | Alinhada | Botão reconectar preservando redirecionamento | **Média** | `portal/src/app/sessao-expirada/page.tsx` | 🟢 Conforme |
| **29** | Confirmações Críticas | Componente `CriticalConfirmationModal` | Modal de confirmação com digitação do nome ou ação irreversível | Alinhada | Previne exclusão acidental e cancelamentos involuntários | **Média** | `portal/src/components/ui/CriticalConfirmationModal.tsx` | 🟢 Conforme |
| **30** | Visualização de PDFs | Modal / Rota de visualização | Visualizador integrado de comprovante de agendamento e checklist | Alinhada | Download de PDF em conformidade com RNF-09 | **Média** | `portal/src/components/features/scheduling/PdfViewerModal.tsx` | 🟢 Conforme |

---

## 3. Principais Divergências e Plano de Correção Imediato

### Divergência 1: Menu Ajuda em Branco (Prioridade Crítica)
- **Problema:** A barra de navegação superior (`GovBar.tsx`) continha link para `/ajuda`, que não existia na pasta `portal/src/app/`, exibindo erro 404 / tela branca.
- **Correção:** Criação da página `portal/src/app/ajuda/page.tsx` com guia passo a passo, cards de orientação (Cadastro, Busca de Serviços, Agendamento Presencial, Acompanhamento de Protocolos e FAQ) e canais de suporte transparentes.

### Divergência 2: Identificação Institucional e Acadêmica (Header e Footer)
- **Problema:** O canto superior esquerdo continha "BRASIL • GOVERNO DE ALAGOAS" e o rodapé indicava parceria institucional não homologada.
- **Correção:**
  - Substituição no Header/GovBar pelo nome oficial: **"SOSP • Sistema de Orientação para Serviços Públicos"**.
  - No Footer, inserção do texto obrigatório: **"Projeto acadêmico desenvolvido por estudantes do CESMAC."** juntamente com aviso institucional de que se trata de projeto acadêmico e link externo informativo para `https://www.gov.br/`.
  - Configuração do favicon oficial com o ícone da bússola do SOSP.

### Divergência 3: Meus Agendamentos para Visitante Não Logado (Prioridade Crítica)
- **Problema:** Usuários anônimos ao acessar `/cidadao/meus-agendamentos` visualizavam agendamentos pré-carregados do mock `citizen-001`.
- **Correção:** 
  - Verificação de sessão antes da renderização.
  - Se anônimo: zero agendamentos, zero chamadas à API, exibindo empty state com o título `"Seus agendamentos em um só lugar"` e subtítulo `"Entre na sua conta ou cadastre-se para visualizar, acompanhar e gerenciar seus agendamentos."` e os botões `"Entrar na minha conta"` e `"Criar conta"`.
  - Se autenticado sem agendamentos: `"Você ainda não possui agendamentos."` e botão `"Explorar serviços"`.
  - Zeração de agendamentos fictícios no estado inicial do mock (`MOCK_APPOINTMENTS = []`).

### Divergência 4: Busca de Serviços com Paginação de 5 Itens
- **Problema:** Listagem configurada para 10 itens por página.
- **Correção:** Ajuste no client-side para apresentar **5 itens por página**, com cálculo dinâmico de páginas, navegação fluida, preservação de filtros combináveis (`AND`) e total acessibilidade.

### Divergência 5: Campo Sexo/Gênero com Opção "Outro"
- **Problema:** O formulário de cadastro oferecia a opção "Outro", mas não exibia campo para descrição textual.
- **Correção:** Inclusão de campo condicional `"Qual? (descreva sua identidade de gênero)"`, exibido imediatamente abaixo com animação suave e atributos `aria-expanded` para leitor de tela.

### Divergência 6: Checklist e Força de Senha no Cadastro
- **Problema:** Indicador de força genérico sem os 5 critérios oficiais da política de senha do backend.
- **Correção:** Implementação de checklist dinâmico com 5 regras verificadas em tempo real (8 caracteres, maiúscula, minúscula, número, caractere especial), barra horizontal de progresso de 4 estágios e badge textual ("Fraca", "Razoável", "Boa", "Forte").

### Divergência 7: Separação de Acesso Cidadão e Servidor/Gestor
- **Problema:** Aba de alternância `Cidadão | Servidor/Gestor` na tela de login comum.
- **Correção:** Remoção das abas da página principal `/login`, deixando-a focada no cidadão. Inclusão de link discreto `"É servidor ou gestor? Acesse o portal institucional."` apontando para `/login/institucional`. Redirecionamento automático e seguro após login de acordo com o `role` do usuário.

### Divergência 8: Edição Completa de Órgãos no Painel Administrativo
- **Problema:** Painel de órgãos permitia apenas desativação lógica, sem formulário de edição de órgãos existentes.
- **Correção:** 
  - Backend: Criação de endpoint `GET /api/v1/agencies/{id}` e `PATCH /api/v1/agencies/{id}` com controle de permissão RBAC e auditoria `auditEvent`.
  - Frontend: Inclusão do botão "Editar", modal de edição com validação, feedback de sucesso e cancelamento seguro sem perda de dados.
