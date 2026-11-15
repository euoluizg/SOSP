# Módulo: Scheduling (Agendamento e Fila Operacional)

## 1. Requisitos Cobertos
- **RF-08:** Agendamento presencial 100% interno no SOSP.
- **RF-09:** Acompanhamento do protocolo em tempo real e upload de anexos.
- **RN-18:** Slots de atendimento com duração padrão de 30 minutos dentro do expediente da unidade.
- **RN-19:** Desconto automático de feriados, recessos e finais de semana.
- **RN-20:** Protocolo determinístico no formato oficial `AAAAMMDD-XXXX`.
- **RN-21:** Bloqueio de agendamento duplicado para o mesmo cidadão e serviço com status pendente.
- **RN-22:** Cancelamento ou remarcação permitidos com antecedência mínima de 24 horas.
- **RN-23:** Registro oficial de não comparecimento (falta / ausente) pelo servidor público.

## 2. Ciclo de Vida do Atendimento no Painel do Servidor
1. **Aguardando (`waiting`):**
   - Ações disponíveis: **Chamar** (`in_progress`), **Ausente** (`no_show`), **Cancelar** (`cancelled`).
2. **Em Atendimento (`in_progress`):**
   - Ações disponíveis: **Concluir** (`completed`), **Ausente** (`no_show`), **Cancelar** (`cancelled`).
3. **Estados Terminais Permanentes:**
   - **Concluído (`completed`):** Atendimento executado com sucesso e documentação verificada.
   - **Ausente (`no_show`):** Registro de ausência efetuado conforme RN-23.
   - **Cancelado (`cancelled`):** Atendimento cancelado com motivo arquivado.

## 3. Isolamento Operacional e Segurança
- Servidores operacionais acessam exclusivamente a fila e os relatórios da sua unidade de lotação (`unitId`), sem acesso aos módulos administrativos de Gestão Geral (`/admin/*`).
- Identificação do atendente e matrícula exibidas dinamicamente a partir da sessão ativa.

