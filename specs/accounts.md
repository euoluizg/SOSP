# Módulo: Accounts (Contas e Autenticação)

## 1. Requisitos Cobertos
- **RF-01:** Cadastro de Cidadão com validação de 19 campos cadastrais, CPF, idade mínima de 12 anos e integração ViaCEP.
- **RF-02:** Autenticação local para Cidadãos, Servidores e Administradores com hash Argon2id + salt.
- **RN-28:** Expiração de sessão após 30 minutos de inatividade.
- **RN-29:** Bloqueio temporário de 5 minutos após 5 tentativas incorretas consecutivas.
- **RN-30:** Recuperação de senha por código de 6 dígitos enviado por e-mail com validade de 15 minutos.
- **RN-35 / RN-36:** Matriz de controle de acesso (RBAC) com escopo restrito por órgão e unidade.

## 2. Modelos e Entidades
- `Citizen`: Tabela `accountsCitizen` (dados pessoais, endereço, CPF, senha Argon2id).
- `InternalUser`: Tabela `accountsInternalUser` (servidores, gestores e administradores, matrículas `registrationNumber`).
- `Session`: Tabela `accountsSession` (tokens de sessão ativos, hash de token, revogação).
- `PasswordReset`: Tabela `accountsPasswordReset` (códigos de 6 dígitos com hash e timestamp).

## 3. Identificação e Autenticação de Servidores
- Servidores autenticam-se com **CPF** ou **Matrícula Funcional** (ex: `202XXXXX`, `SSP-1001`).
- Primeiro acesso interceptado para troca compulsória de senha temporária.
- Servidor operacional vinculado estritamente à sua `unitId` de lotação.

