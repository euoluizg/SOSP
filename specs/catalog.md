# Módulo: Catalog (Catálogo de Serviços e Unidades)

## 1. Requisitos Cobertos
- **RF-03 / RF-04:** Catálogo unificado de serviços públicos com categorização oficial.
- **RF-05:** Ficha orientativa estruturada com 8 blocos informativos.
- **RN-01 / RN-02:** Versionamento imutável de fichas com controle de rascunho e publicação.
- **RN-06 a RN-12:** Regras de exibição de documentos obrigatórios/opcionais, prazos e coordenadas geográficas de unidades.

## 2. Modelos
- `Agency`: Tabela `catalogAgency` (órgãos públicos com sigla e esfera).
- `Unit`: Tabela `catalogUnit` (unidades físicas de atendimento com expediente e capacidade).
- `Service`: Tabela `catalogService` (serviços com canal, categoria e prazo médio).
- `ServiceDocument`: Tabela `catalogServiceDocument` (documentos exigidos).

