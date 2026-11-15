# Módulo: Audit (Auditoria e Trilha Imutável)

## 1. Requisitos Cobertos
- **RN-39:** Registro obrigatório de eventos administrativos na tabela `auditEvent` contendo ator, IP, ação, tabela alvo, estado anterior e novo estado.
- **RN-40:** Proibição de exclusão física (`DELETE`) em tabelas de negócio; aplicação de desativação lógica (`isActive = false`, `deletedAt = NOW()`).
- **RS-05:** Trilha de auditoria imutável (sem possibilidade de atualização ou exclusão de logs).

