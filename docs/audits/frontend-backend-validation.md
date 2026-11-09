# Relatório de Integração Full Stack, Contratos e Validação de Perfis — SOSP

> **Escopo:** Frontend Next.js 15, Backend Django 5 + DRF, Banco de Dados, RBAC, Contratos e Testes  
> **Equipe Especialista:** Hermes Agent • Backend Lead • React CTO • Test Lead • Security Tester  
> **Data:** Novembro de 2026

---

## 1. Visão Geral da Arquitetura e Contratos

O SOSP opera sob arquitetura de Monólito Modular (`ADR-001`), onde o portal Frontend consome exclusivamente a API REST (`/api/v1/...`) disponibilizada pelo Backend Django REST Framework.

### 1.1. Contrato da Nova Funcionalidade: Edição de Órgãos Públicos
Para atender à necessidade do gestor de editar órgãos cadastrados sem depender de ações destrutivas ou exclusão de registros:

- **Endpoint:** `PATCH /api/v1/agencies/{id}` (e `GET /api/v1/agencies/{id}`)
- **Autenticação:** Bearer Token via header `Authorization`
- **Permissão RBAC:** Perfis institucionais autorizados (`admin`, `superadmin`, `gestor` associado ao órgão)
- **Payload Aceito:**
  ```json
  {
    "name": "Nome Atualizado do Órgão",
    "acronym": "SIGLA",
    "sphere": "state",
    "description": "Nova descrição das atribuições do órgão."
  }
  ```
- **Auditoria Transversal:** Todo update gera registro em `auditEvent` (`action = 'UPDATE_AGENCY'`), contendo o estado anterior (`beforeState`) e o estado novo (`afterState`).
- **Respostas de Erro:** Padrão RFC 7807 (`application/problem+json`).

---

## 2. Usuários Sintéticos de Demonstração e Matriz de Acesso aos Três Painéis

Para assegurar testes completos das três experiências sem dados reais de pessoas físicas e com **zero agendamentos iniciais**:

### Acesso 1 — Perfil Cidadão (Orientação, Agendamento e Acompanhamento)
- **Rota de Login:** `/login`
- **Rota do Painel:** `/cidadao/meus-agendamentos`
- **Funcionalidades:** Busca de serviços, guia e checklist de documentos, agendamento de horários em unidades Já!, acompanhamento de protocolos `AAAAMMDD-XXXX`, cancelamento até 24h antes.
- **Conta Demonstrativa 1:**
  - *Identificação:* `Cidadão de Testes`
  - *CPF Sintético:* `111.444.777-05`
  - *Papel:* `citizen`
  - *Estado Inicial de Agendamentos:* 0 (vazio)
- **Conta Demonstrativa 2 (Segregação de Dados):**
  - *Identificação:* `Maria Santos Silva`
  - *CPF Sintético:* `222.555.888-09`
  - *Papel:* `citizen`
  - *Estado Inicial de Agendamentos:* 0 (vazio)

### Acesso 2 — Perfil Servidor Público (Operação e Atendimento Presencial)
- **Rota de Login:** `/login/institucional` (com perfil Servidor)
- **Rota do Painel:** `/servidor/painel` e `/servidor/atendimento`
- **Funcionalidades:** Fila de atendimento diária da unidade, conferência de documentos de agendamento, confirmação de presença, registro de não-comparecimento, relatórios da sua unidade.
- **Conta Demonstrativa 1 (Unidade Centro - SSP):**
  - *Identificação:* `João Servidor Central`
  - *CPF Sintético:* `333.666.999-01`
  - *Papel:* `server`
  - *Lotação:* `agencyId: orgao-ssp`, `unitId: unidade-centro`
- **Conta Demonstrativa 2 (Unidade Farol - DETRAN):**
  - *Identificação:* `Ana Servidora Farol`
  - *CPF Sintético:* `444.777.000-02`
  - *Papel:* `server`
  - *Lotação:* `agencyId: orgao-detran`, `unitId: unidade-farol`

### Acesso 3 — Perfil Gestor / Governança (Administração Institucional)
- **Rota de Login:** `/login/institucional` (com perfil Gestor / Admin)
- **Rota do Painel:** `/admin/orgaos` e `/admin/servicos`
- **Funcionalidades:** Gerenciamento completo de órgãos públicos (cadastro, consulta, edição e desativação lógica), gestão de unidades, publicação de serviços, auditoria imutável.
- **Conta Demonstrativa 1 (Gestor Institucional SSP):**
  - *Identificação:* `Carlos Gestor SSP`
  - *CPF Sintético:* `555.888.111-03`
  - *Papel:* `gestor`
  - *Lotação:* `agencyId: orgao-ssp`
- **Conta Demonstrativa 2 (Administrador Geral SOSP):**
  - *Identificação:* `Admin SOSP Geral`
  - *CPF Sintético:* `000.111.222-04`
  - *Papel:* `superadmin`
  - *Escopo:* Acesso global irrestrito a todos os órgãos e trilhas de auditoria.

> 🔒 **Segurança das Contas:** Senhas temporárias sintéticas geradas via Argon2id. Nenhuma senha real ou segredo é gravado em arquivos versionados.

---

## 3. Catálogo Oficial de Órgãos e Serviços (Dados Iniciais Cadastrais)

O sistema mantém estritamente os órgãos públicos do escopo de Alagoas definidos nos requisitos oficiais:
1. **SSP — Secretaria de Estado da Segurança Pública:**
   - *Serviço:* Emissão da Carteira de Identidade Nacional (CIN / RG).
2. **DETRAN-AL — Departamento Estadual de Trânsito:**
   - *Serviço:* Renovação da Carteira Nacional de Habilitação (CNH).
3. **SEFAZ-AL — Secretaria de Estado da Fazenda:**
   - *Serviço:* Emissão de Certidão Negativa de Débitos Estaduais (CND).
4. **SEDUC — Secretaria de Estado da Educação:**
   - *Serviço:* Matrícula e Transferência na Rede Escolar Estadual.
5. **SESAU — Secretaria de Estado da Saúde:**
   - *Serviço:* Agendamento de Consultas Especializadas e Exames de Alta Complexidade.

---

## 4. Bateria de Testes e Portão Pré-PR

| Suíte de Testes | Ferramenta / Comando | Qtd Cenários | Resultado Esperado | Status |
|---|---|---|---|---|
| **Testes Unitários de Frontend** | `cd portal && npm test` | 54 testes | 100% de aprovação | ✅ GO |
| **Checagem de Tipos TypeScript** | `cd portal && npm run typecheck` | Global | 0 erros | ✅ GO |
| **Testes de Backend Django** | `cd backend && pytest -q` | 148+ testes | 100% de aprovação | ✅ GO |
| **Django System Check** | `cd backend && python manage.py check` | 9 módulos | 0 problemas | ✅ GO |
| **Navegação e Rotas** | Validação de `/ajuda`, `/login`, `/cidadao/meus-agendamentos` | 6 fluxos | 100% de conformidade | ✅ GO |
| **Acessibilidade WCAG 2.1 AA** | Contraste e teclado | Todas as páginas | Sem violações impeditivas | ✅ GO |
