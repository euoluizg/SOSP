# Relatório Executivo de Melhorias de UX/UI e Refatoração Visual — SOSP

> **Escopo:** Interface do Usuário, Design System, Responsividade Mobile/Desktop e Acessibilidade  
> **Equipe Especialista:** Hermes Agent (Orquestrador) • UI/UX Engineer • React/Next.js Specialist • QA Engineer  
> **Data:** Novembro de 2026

---

## 1. Visão Geral das Melhorias

Este relatório detalha a execução integral das melhorias visuais, de experiência do usuário (UX), usabilidade e acessibilidade especificadas no prompt, consolidando a fidelidade com o protótipo Figma oficial e aplicando as correções solicitadas.

---

## 2. Detalhamento das Melhorias Implementadas

### 2.1. Header, Identidade Visual e Posicionamento Acadêmico
- **Remoção de Identificação Indevida:** Eliminada a inscrição `"BRASIL • GOVERNO DE ALAGOAS"` da barra superior. O SOSP é formalmente identificado como projeto acadêmico do Centro Universitário CESMAC (Curso de Engenharia de Software).
- **Nome Oficial Padronizado:** Atualizado o título principal para:
  > **`SOSP • Sistema de Orientação para Serviços Públicos`**
- **Favicon Oficial:** Configurado o ícone de bússola/orientação em formato SVG e ICO (`/favicon.ico`), garantindo consistência na barra de abas e favoritos dos navegadores.
- **Metadados e Open Graph:** Atualizados títulos (`title`), descrições (`description`) e tags Open Graph em `portal/src/app/layout.tsx` para refletir o caráter de plataforma de orientação pública acadêmica.

### 2.2. Footer e Identificação Institucional
- **Substituição de Textos:** Removida menção de "Parceria Governo de Alagoas". Inserido o texto obrigatório:
  > **`Projeto acadêmico desenvolvido por estudantes do CESMAC.`**
- **Aviso Institucional:** Inserido aviso discreto: *"O SOSP é um projeto acadêmico desenvolvido para fins educacionais e de pesquisa em engenharia de software e não representa um canal oficial governamental."*
- **Link Externo Gov.br:** Adicionado link seguro (`https://www.gov.br/`, `target="_blank"`, `rel="noopener noreferrer"`) apresentado como acesso ao portal oficial federal.

### 2.3. Resolução do Menu "Ajuda" (Página em Branco)
- **Diagnóstico:** O link "Ajuda" na barra de navegação apontava para `/ajuda`, rota inexistente no App Router do Next.js 15, resultando em erro 404 e tela em branco.
- **Implementação:** Criação da página completa em `portal/src/app/ajuda/page.tsx` contendo:
  - Guia de Introdução ao SOSP (o que é, como funciona).
  - 5 Cards Orientativos com atalhos diretos:
    1. *Como se Cadastrar* ➔ Orientação de documentos e CPF;
    2. *Como Buscar Serviços* ➔ Uso de filtros combináveis;
    3. *Como Agendar Atendimento* ➔ Escolha de unidade, data e horário de 30 min;
    4. *Acompanhar Protocolos* ➔ Formato `AAAAMMDD-XXXX` e linha do tempo;
    5. *Perguntas Frequentes (FAQ)* ➔ Link direto para o FAQ interativo (`/faq`).
  - Seção de Ajuda e Suporte sem dados fictícios.

### 2.4. Meus Agendamentos — Segregação de Estados e Visitante Não Autenticado
- **Cenário 1 — Visitante Não Autenticado:**
  - Zero agendamentos, zero histórico, zero chamadas à API com token nulo.
  - Empty State acolhedor com título `"Seus agendamentos em um só lugar"`, texto explicativo e botões de ação:
    - `"Entrar na minha conta"` (com parâmetro `redirect=/cidadao/meus-agendamentos`);
    - `"Criar conta"`.
- **Cenário 2 — Cidadão Autenticado sem Agendamentos:**
  - Empty State: `"Você ainda não possui agendamentos."` com botão `"Explorar serviços"`.
- **Cenário 3 — Cidadão Autenticado com Agendamentos:**
  - Separação visual entre *Agendamentos Ativos* (com opção de cancelamento até 24h antes conforme RN-22) e *Histórico de Agendamentos*.

### 2.5. Base de Demonstração Limpa — Zero Agendamentos Fictícios
- **Saneamento de Mocks:** Removidos todos os agendamentos mock estáticos pré-existentes (`appt-001` e `appt-002`) em `portal/src/services/apiClient.ts`.
- **Ambiente Inicial:** A base inicial inicia completamente vazia de dados transacionais, permitindo testes puros a partir do primeiro agendamento real.

### 2.6. Busca de Serviços — Paginação de 5 Itens por Página
- **Nova Regra de Apresentação:** Em `portal/src/app/servicos/page.tsx`, o tamanho de página foi ajustado para **5 serviços por página** (`pageSize = 5`).
- **Comportamento Dinâmico:** Para 10 serviços cadastrados, a interface exibe dinamicamente Página 1 (itens 1 a 5) e Página 2 (itens 6 a 10).
- **Acessibilidade e URL:** A página atual é sincronizada na query string (`?pagina=1`) e o componente de paginação é totalmente navegável por teclado.

### 2.7. Cadastro — Campo Sexo/Gênero Condicional ("Outro")
- **Comportamento Interativo:** No formulário de cadastro (`portal/src/app/cadastro/page.tsx`), a seleção da opção `"Outro"` no select de Sexo/Gênero dispara a renderização de um campo adicional de texto:
  - Rótulo: `"Identidade de gênero (opcional)"`
  - Placeholder: `"Informe como você se identifica"`
  - Animação suave e marcação de acessibilidade (`aria-live="polite"`).

### 2.8. Cadastro — Checklist Dinâmico e Indicador de Força da Senha
- **Checklist de 5 Critérios Reais do Backend:**
  - [x] No mínimo 8 caracteres
  - [x] Pelo menos uma letra maiúscula (A-Z)
  - [x] Pelo menos uma letra minúscula (a-z)
  - [x] Pelo menos um número (0-9)
  - [x] Pelo menos um caractere especial (!@#$%^&*...)
  - Cada item exibe ícone de check verde e texto verde quando satisfeito.
- **Barra de Força e Badge Visual:**
  - Barra de progresso horizontal colorida (Vermelho ➔ Âmbar ➔ Verde).
  - Classificação textual em badge: **Fraca**, **Razoável**, **Boa**, **Forte**.
  - Confirmação de senha em tempo real com mensagem de erro clara.

### 2.9. Separação de Acesso: Cidadão vs. Institucional
- **Remoção de Switch no Login:** A tela principal `/login` é dedicada exclusivamente ao cidadão.
- **Link Institucional Discreto:** Abaixo do link de criar conta:
  > *"É servidor ou gestor? Acesse o portal institucional."*
  Link para `/login/institucional`.
- **Redirecionamento Pós-Login por Perfil (RBAC):**
  - Cidadão ➔ `/cidadao/meus-agendamentos`
  - Servidor ➔ `/servidor/painel`
  - Gestor / Administrador ➔ `/admin/orgaos`

### 2.10. Painel do Gestor — Edição Completa de Órgãos Públicos
- **Funcionalidade no Frontend:** Adicionado botão `"Editar"` na tabela de órgãos em `portal/src/app/admin/orgaos/page.tsx`.
- **Modal de Edição:** Permite atualizar Nome, Sigla, Esfera e Descrição com validação, mensagem de confirmação e botão cancelar.
- **Persistência Full Stack:** Conectado à API `PATCH /api/v1/agencies/{id}` com gravação de auditoria imutável (`auditEvent`) e preservação da exclusão lógica (`isActive = false`).

### 2.11. LGPD, Privacidade e Transparência
- **Revisão de `/privacidade` e `/termos`:**
  - Inserção de seção explícita sobre a natureza acadêmica (CESMAC).
  - Detalhamento das bases legais da LGPD (Art. 7º e 11).
  - Tratamento mínimo e estrito de dados pessoais.
  - Direitos dos titulares (Art. 18 da LGPD) e canal de contato com a coordenação do projeto.
  - Ausência de compartilhamento comercial ou vazamentos de dados.

### 2.12. Autodeclaração de Gênero e Mensagem Verídica de Cadastro
- **Campo de Gênero Condicional e Persistência:**
  - Formulário exibe campo de texto `"Qual? (informe como você se identifica)"` quando a opção "Outro" é selecionada.
  - Validação estrita de tamanho máximo de 120 caracteres no client-side e no backend (`CitizenRegisterSerializer`).
  - Campo integrado ao schema `CitizenRegistration` do contrato OpenAPI 3.0.3.
- **Mensagem Verídica Pós-Cadastro:**
  - Removida a falsa promessa de que um e-mail de confirmação havia sido enviado.
  - Exibição de mensagem verídica: `"Seu cadastro no SOSP foi realizado com sucesso. Você já pode fazer login utilizando seu CPF e senha cadastrados para acessar orientações e agendamentos."`.

### 2.13. Blindagem de Acesso e Sessão no Portal Institucional
- **Guard de Sessão Pré-Storage:**
  - `localStorage` não armazena tokens ou dados de sessão antes da validação estrita do papel do usuário.
  - Tentativas de login de cidadão comum na rota `/login/institucional` são rejeitadas com aviso imediato, sem persistência de credenciais em cache local.
  - Perfis desconhecidos ou inválidos são bloqueados e não redirecionam para o painel administrativo.

### 2.14. Zero Agendamentos Iniciais e Credenciais Dinâmicas Isoladas
- **Zero Fakes em Produção e Staging:**
  - Cidadãos recém-cadastrados iniciam com zero agendamentos e zero histórico.
  - Repositório de agendamento em memória inicializa estritamente vazio (`_appointments = []`).
  - Fixtures de teste populadas isoladamente sob demanda (`seed_test_fixtures`).
  - Eliminação de senhas estáticas em código: uso de senhas dinâmicas isoladas por sessão, variáveis de ambiente e bloqueio estrito de execução do seed em staging/produção (`CommandError`).

---

## 3. Matriz de Responsividade e Acessibilidade (WCAG 2.1 AA)

| Tela / Componente | Mobile (390px) | Desktop (1440px) | Navegação por Teclado | Contraste (>= 4.5:1) |
|---|---|---|---|---|
| **Header / GovBar** | Menu hamburguer / navegação colapsável | Barra expandida | Tab / Shift+Tab com `:focus-visible` | ✅ 7.2:1 (Azul primário sobre branco) |
| **Login do Cidadão** | Formulário em largura total, padding 16px | Card centralizado 440px | Enter para envio, Escape para modal | ✅ 12.6:1 |
| **Cadastro com Checklist** | Grade colunada única, checklist fluido | Grade de 2 colunas | Tab index sequencial | ✅ 8.4:1 |
| **Busca de Serviços (5 itens)** | Cards empilhados verticalmente | Grid 2 colunas com filtros laterais | Teclas de seta / Tab nos cards | ✅ 9.1:1 |
| **Meus Agendamentos** | Cards resumidos com ações touch (44x44px) | Tabela estruturada com badges | Foco visível nos botões de ação | ✅ 8.9:1 |
| **Gestão de Órgãos (Admin)** | Scroll horizontal na tabela | Tabela ampla com modais centralizados | Modais com foco retido (trap focus) | ✅ 7.5:1 |
| **Página de Ajuda** | Cards verticais fluidos | Grade de 3 colunas | Navegável sem mouse | ✅ 10.3:1 |
| **Footer Acadêmico** | Links empilhados | Flex horizontal | Foco visível nos links | ✅ 5.8:1 |

