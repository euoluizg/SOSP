# Product Requirements Document (PRD) — SOSP

**Sistema de Orientação para Serviços Públicos (SOSP)**  
*Plataforma Integrada de Orientação, Checklist de Documentos, Agendamento e Acompanhamento de Protocolos*

---

## 1. Visão Geral e Propósito

O **SOSP** é uma plataforma pública desenvolvida para transformar a relação entre cidadãos e a administração pública estadual. Ele orienta de forma clara os requisitos de serviços públicos, fornece checklists interativos de documentos, possibilita agendamento presencial controlado por capacidade e guichê, e oferece rastreamento em tempo real de protocolos.

- **Público-alvo:**
  1. **Cidadão:** Consulta catálogo, prepara documentos, agenda horário e acompanha protocolo.
  2. **Servidor Operacional:** Opera a fila de guichê em tempo real, valida comparecimento, atende ou registra ausência/cancelamento de agendamentos da sua unidade.
  3. **Gestor Institucional e Administrador:** Gerenciam órgãos, unidades, serviços, FAQs, usuários internos e visualizam relatórios gerenciais e trilha de auditoria.

---

## 2. Escopo do MVP e Funcionalidades Centrais

### 2.1. Funcionalidades Desenvolvidas (Ponta a Ponta)

1. **Cadastro do Cidadão (`RF-01`):**
   - 19 campos cadastrais com validação rigorosa de CPF, idade mínima de 12 anos, campos de PCD com detalhamento condicional e endereço com integração ViaCEP.
   - Hash de credenciais com `Argon2id + salt` e proteção contra força bruta (`RN-29`).

2. **Autenticação, Lockout e Primeiro Acesso (`RF-02`, `ADR-003`):**
   - Login por **CPF + senha** para Cidadãos, e por **CPF ou Matrícula funcional (ex: 202XXXXX, SSP-1001)** para Servidores/Gestores.
   - Bloqueio automático de 5 minutos após 5 tentativas falhas consecutivas (`RN-29`).
   - Sessão segura com expiração após 30 minutos de inatividade (`RN-28`).
   - Interceptação de primeiro acesso com obrigatoriedade de troca de senha provisória.
   - Recuperação de senha via código de 6 dígitos enviado por e-mail com validade de 15 minutos (`RN-30`).

3. **Busca e Filtros Combinados de Serviços (`RF-03`, `RF-04`):**
   - Busca textual com PostgreSQL full-text (`tsvector` + `unaccent`).
   - Filtros combináveis por interseção (`AND`): Categoria, Órgão, Canal (Online, Presencial, Híbrido) e Município (`RN-04`).
   - Paginação padrão de 10 itens por página (`RN-05`).
   - Mensagem orientativa de estado vazio: *"Nenhum serviço encontrado. Tente outro termo ou categoria."* (`RN-13`).

4. **Ficha Orientativa do Serviço (`RF-05`):**
   - Exibição estruturada dos 8 blocos informativos: *O que é*, *Quem tem direito*, *O que levar*, *Como fazer*, *Onde fazer*, *Quando*, *Quanto custa* e *Quanto demora*.
   - Diferenciação clara entre documentos obrigatórios e opcionais (`RN-09`).
   - Exibição de mapa interativo somente quando a unidade possui coordenadas de latitude/longitude válidas (`RN-10`).

5. **Guia Passo a Passo e Checklist de Documentação (`RF-06`, `RF-07`):**
   - Checklist interativo de documentos com persistência do progresso no banco por CPF (`RN-15`).
   - Emissão e download de comprovante em PDF com QR Code de autenticidade.

6. **Agendamento Presencial e Geração de Protocolo (`RF-08`):**
   - Cálculo dinâmico de slots de 30 minutos (`RN-18`) considerando expediente da unidade e exclusão de feriados/dias não úteis (`RN-19`).
   - Bloqueio de agendamento duplicado para o mesmo cidadão e serviço com status pendente (`RN-21`).
   - Chave de idempotência (`Idempotency-Key`) em transações atômicas para evitar duplicidade de concorrência.
   - Geração determinística de protocolo no padrão oficial `AAAAMMDD-XXXX` (`RN-20`).

7. **Acompanhamento de Protocolo e Anexos (`RF-09`):**
   - Linha do tempo visual dos estados de atendimento (Recebido -> Em Análise -> Aguardando Documento -> Concluído).
   - Upload de anexos comprobatórios (PDF, PNG, JPG até 10 MB) com assinatura de URL de acesso temporário.

8. **Painel do Servidor e Gestão de Fila Operacional:**
   - Fila em tempo real por guichê com controle de atendimento: **Chamar** (`in_progress`), **Ausente** (`no_show` — `RN-23`), **Concluir** (`completed`) e **Cancelar** (`cancelled`).
   - Persistência contínua do status de atendimento.
   - Isolamento estrito de RBAC: servidores acessam exclusivamente seu painel e relatórios operacionais da unidade designada, sem acesso às rotas de Gestão Geral (`/admin/*`).
   - Identificação dinâmica do atendente com base na sessão autenticada.

9. **Gestão Geral e Back-office:**
   - CRUD administrativo com desativação lógica (`isActive = false`, `deletedAt = NOW()`) de órgãos, unidades e serviços (`RN-40`).
   - Trilha transversal de auditoria imutável em `auditEvent` (`RN-39`).

---

## 3. Matriz de Requisitos Não-Funcionais e Segurança

- **RNF-01 (Desempenho):** Tempo de resposta da API de busca < 300 ms.
- **RNF-02 (Disponibilidade):** Arquitetura sem estado (`stateless`) pronta para escalabilidade horizontal.
- **RNF-03 (Segurança):** RBAC estrito com prevenção a IDOR/BOLA e enumeração de recursos (retorno `404` em vez de `403` para cidadão consultando dados de terceiros).
- **RNF-04 (LGPD):** Mascaramento de CPF em logs e telas de auditoria; trilha completa de eventos de tratamento de dados.
- **RNF-05 (Responsividade e Acessibilidade):** 100% responsivo para resoluções mobile (390 px) e desktop (1440 px), aderente ao padrão **WCAG 2.1 nível AA**.

---

## 4. Escopo da Versão 2.0 (Desligado por Feature Flags)

- `RF-10` (Avaliações e Comentários 1–5 estrelas): `FEATURE_REVIEWS_ENABLED=false`.
- `RF-13` (Notificações Push, SMS e WhatsApp): `FEATURE_PUSH_ENABLED=false`, `FEATURE_SMS_ENABLED=false`, `FEATURE_WHATSAPP_ENABLED=false`.
- Integração OAuth com Gov.br: Exibe modal informativo explicativo com fallback para credenciais locais.

