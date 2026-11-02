# ADR-003 — Autenticação Gov.br, login interno e RBAC

- **Status:** Aceito
- **Data:** 29/10/2026
- **Decisores:** Arthur Franco e Luiz Gustavo — CESMAC
- **Substitui:** —
- **Substituído por:** —

## Contexto

O sistema tem dois públicos com necessidades de identidade diferentes:

- **Cidadão:** precisa de uma conta para agendar, anexar documentos e acompanhar protocolos. A API oficial do Gov.br (OIDC) exige autorização/credenciamento institucional que o projeto não tem no momento, inviabilizando a integração no MVP. O cidadão faz cadastro manual com CPF + senha.
- **Servidor e administrador:** são usuários internos, com matrícula funcional, órgão de lotação e permissões granulares. Não têm conta Gov.br de cidadão e precisam de login local.

O RF-02 original descreve login por CPF e senha para todos, mas o documento de arquitetura recomenda Gov.br para o cidadão. O projeto adota dois regimes: **MVP com autenticação local** e **v2.0 com Gov.br OIDC como alternativa** (divergência **D10** no [Pilar 1](../01-product-specs.md#7-matriz-de-divergências)).

Além disso, o sistema lida com dados pessoais e sensíveis (PCD), o que exige menor privilégio, auditoria e sessão curta.

## Decisão

### Cidadão — MVP (v1.0)

- Cadastro manual com **CPF + senha**, senha em **Argon2id** com salt por usuário.
- Senha mínima de 8 caracteres, com ao menos uma letra maiúscula, um número e um caractere especial.
- Recuperação por código de 6 dígitos enviado ao e-mail do cidadão, válido por 15 minutos.
- Bloqueio de 5 minutos após 5 tentativas erradas, com mensagem genérica "CPF ou senha inválidos".
- A senha segue as mesmas regras de segurança dos servidores: Argon2id + salt, sessão de 30 min, bloqueio após 5 tentativas.

### Cidadão — v2.0 (Gov.br OIDC)

- Autenticação via **Gov.br com OpenID Connect**, fluxo **Authorization Code + PKCE**, como alternativa ao login local.
- O botão **"Entrar com Gov.br"** existe na interface desde o MVP, mas exibe modal informativo de "implementação futura" quando clicado.
- O comportamento real do OIDC é controlado pela flag `FEATURE_GOVBR_INTEGRATION_ENABLED` (ver [ADR-007](ADR-007-feature-flags.md)).
- O `code_verifier` fica no servidor; o navegador só vê o `code_challenge`.
- O vínculo é feito por `govbrSubjectId` (`sub` do `id_token`), nunca por e-mail ou CPF.
- O SOSP **nunca recebe nem armazena a senha do cidadão** via Gov.br.
- O `id_token` é validado contra o JWKS do provedor, com verificação de assinatura, `iss`, `aud`, `exp` e `nonce`.

### Servidor e administrador

- Login local com **CPF + senha**, senha em **Argon2id** com salt por usuário.
- Senha temporária de 10 caracteres, validade de 48 horas e troca obrigatória no primeiro acesso.
- Recuperação por código de 6 dígitos enviado ao e-mail corporativo, válido por 15 minutos.
- Bloqueio de 5 minutos após 5 tentativas erradas, com mensagem genérica "CPF ou senha inválidos".

### Sessão

- Cookie `HttpOnly`, `Secure`, `SameSite=Lax`, assinado.
- Expiração por inatividade de **30 minutos**, renovada a cada requisição autenticada.
- Logout invalida a sessão no servidor, não apenas o cookie.
- CSRF token por sessão, exigido em métodos mutáveis.

### Autorização

- **RBAC** com quatro papéis efetivos: `citizen`, `servant`, `authorizedServant`, `administrator`.
- O papel `authorizedServant` não é um cadastro separado: é o `servant` com a permissão `canManageCatalog = true`.
- Permissões são verificadas na camada de serviço, não apenas na view.
- Toda decisão de autorização negada gera evento de auditoria.
- Relatórios de servidor são filtrados pelo órgão de lotação; administrador vê todos.

## Consequências positivas

| Consequência | Efeito |
|---|---|
| Cadastro e login funcionam sem dependência externa | MVP pode ser implantado sem credenciamento Gov.br |
| Senha Argon2id + bloqueio de tentativas | Segurança compatível com servidores públicos |
| Fluxo único CPF + senha no MVP | Menos código e testes que dois fluxos simultâneos |
| Login local para servidor | Back-office não depende do Gov.br |
| RBAC granular | Secretarias gerenciam seu catálogo sem virar administrador |
| Auditoria de autorização | Tentativas negadas são rastreáveis |
| Botão Gov.br visível desde o MVP | Usuário já conhece o caminho; a migração para v2.0 é incremental |

## Consequências negativas e trade-offs

| Trade-off | Custo aceito | Mitigação |
|---|---|---|
| Cidadão precisa criar e lembrar mais uma senha | Fricção no cadastro e risco de credencial fraca | Regras de senha (8+ caracteres, complexidade) + Argon2id + recuperação por e-mail |
| Migração para Gov.br na v2.0 pode exigir unificação de contas | Contas locais precisam ser linkadas ao `govbrSubjectId` | Tabela de vínculo futuro já prevista no schema |
| Dois fluxos de login na v2.0 | Mais código e mais testes no futuro | Serviço de sessão comum aos dois fluxos |
| Sessão de 30 min | Cidadão pode precisar relogar no meio do agendamento | Retorno preservado e aviso antes de expirar |
| Senha do cidadão armazenada no SOSP | Aumenta o impacto de um vazamento | Apenas hash Argon2id + salt; nunca texto claro |

## Alternativas descartadas

### Gov.br OIDC como única forma de autenticação no MVP

Descartado porque a API oficial do Gov.br exige autorização/credenciamento institucional que o projeto não possui atualmente. A integração permanece como objetivo da v2.0, com botão na interface já preparado.

### Login social genérico (Google, Facebook)

Não tem validade institucional para um serviço público e não garante CPF verificado. O Gov.br permanece como o provedor oficial na v2.0.

### SSO próprio com SAML

Complexidade desproporcional e fora do padrão adotado pelo governo federal para o cidadão.

### Sessão com JWT no `localStorage`

Expõe o token a XSS e dificulta revogação. Cookie `HttpOnly` com sessão no servidor é mais seguro para o portal.

### Sessão longa de 8 horas

Aumenta a janela de uso indevido em computadores compartilhados (lan houses, bibliotecas). Os 30 minutos do RF-02 são adequados ao contexto.

## Critérios de verificação

| Critério | Como verificar |
|---|---|
| Cadastro rejeita CPF inválido | Teste com CPF com dígito trocado |
| Senha armazenada como hash Argon2id + salt | Inspeção de schema e consulta direta ao banco |
| Sessão expira em 30 min | Teste com relógio controlado |
| Bloqueio após 5 tentativas | Teste de segurança com senha errada repetida |
| Recuperação por código de 6 dígitos | Teste de fluxo completo com e-mail mockado |
| RBAC por rota e por serviço | Teste de autorização por papel |
| Relatório filtrado por órgão | Teste com dois servidores de órgãos distintos |
| Botão Gov.br exibe modal "implementação futura" | Teste de componente com `FEATURE_GOVBR_INTEGRATION_ENABLED=false` |
| Flag Gov.br ligada executa OIDC real | Teste de integração com mock do Gov.br (v2.0) |

## Referências

- [Pilar 1 — Matriz de divergências, D10](../01-product-specs.md#7-matriz-de-divergências)
- [Pilar 3 — Segurança na arquitetura](../03-architecture.md#8-segurança-na-arquitetura)
- Documento de Arquitetura SOSP, seção 6.
- Gov.br — documentação de integração OIDC.
- [ADR-007 — Feature flags para Gov.br OIDC](ADR-007-feature-flags.md)
