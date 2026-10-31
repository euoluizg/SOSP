# ADR-006 — Armazenamento de objetos compatível com S3 (MinIO local, S3 em produção)

- **Status:** Aceito
- **Data:** 31/10/2026
- **Decisores:** Equipe de Engenharia de Software — CESMAC
- **Substitui:** —
- **Substituído por:** —

## Contexto

O SOSP produz e recebe arquivos que não pertencem ao banco relacional:

| Arquivo | Origem | Tamanho típico | Sensibilidade |
|---|---|---|---|
| Comprovante de agendamento (PDF) | Worker de PDF | 100–300 KB | Média (dados do cidadão) |
| Guia + checklist (PDF) | Worker de PDF | 200–500 KB | Baixa (conteúdo público) |
| Anexo de protocolo | Upload do cidadão | até 10 MB | Alta (documento pessoal) |
| Exportação de relatório (CSV/PDF) | Worker de relatórios | 1–20 MB | Média (dados agregados) |
| Avatar do cidadão | Upload do cidadão | até 2 MB | Baixa |

Guardar binário em coluna `bytea` engorda o banco, complica o backup e piora o tempo de resposta. Guardar em disco local amarra o arquivo a uma réplica e quebra o deploy horizontal. O projeto precisa de um storage de objetos com URL assinada, política de retenção e remoção controlada.

O ambiente de desenvolvimento precisa funcionar sem conta em nuvem e sem custo. O ambiente de produção precisa de durabilidade, TLS e credenciais gerenciadas.

## Decisão

### Interface única, provedores trocáveis

Adotamos a **API S3** como interface única de storage. O código da aplicação fala S3; o provedor por trás é configuração, não código.

| Ambiente | Provedor | Configuração |
|---|---|---|
| Local | **MinIO** no `docker-compose` | `AWS_S3_ENDPOINT_URL=http://localhost:9000`, path style |
| Staging | S3 ou **Supabase Storage** (camada S3) | Bucket privado, credenciais no secret manager |
| Produção | S3 ou Supabase Storage | Bucket privado, versionamento e lifecycle |

**Regra:** nenhum módulo de domínio importa SDK de provedor. O acesso passa por uma porta (`storage.put`, `storage.signed_url`, `storage.delete`) implementada com `django-storages`/`boto3`.

### Buckets e visibilidade

| Bucket | Conteúdo | Acesso | Retenção |
|---|---|---|---|
| `sosp-private` | Anexos de protocolo, comprovantes, exports | Somente URL assinada | Anexo: enquanto o protocolo existir; export: 7 dias |
| `sosp-public` | Guias e checklists em PDF | URL assinada de curta duração | 90 dias, regenerável |
| `sosp-avatars` | Avatar do cidadão | URL assinada | Enquanto a conta existir |

**Nenhum bucket é público.** Mesmo o material de orientação é servido por URL assinada, para permitir revogação e auditoria. O portal nunca recebe credencial de storage.

### Upload e download

1. O upload de anexo passa **pelo Django**, não direto do navegador para o storage. O Django valida extensão real, tamanho (≤ 10 MB), assinatura do arquivo e envia ao ClamAV (RS-04).
2. O objeto é gravado com nome opaco (`<uuid>`), sem o nome original no caminho. O nome original fica apenas no metadado do banco.
3. O download é uma URL assinada com TTL de **300 segundos** (`SIGNED_URL_TTL_SECONDS`), gerada sob demanda após autorização.
4. A remoção é lógica no banco e física no storage por rotina de expurgo; o objeto não é apagado antes do prazo de retenção.
5. O worker grava PDFs e exports diretamente no bucket privado e atualiza o status do job.

### Configuração

As variáveis são as do [`.env.example`](../../.env.example):

```bash
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=sosp-local
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_REGION_NAME=us-east-1
AWS_S3_USE_SSL=false
AWS_S3_ADDRESSING_STYLE=path
SIGNED_URL_TTL_SECONDS=300
```

Em produção, `AWS_S3_USE_SSL=true`, `AWS_S3_ADDRESSING_STYLE=virtual` (quando o provedor exigir) e credenciais vindas do secret manager. A aplicação falha no boot se `AWS_STORAGE_BUCKET_NAME` estiver ausente e o storage for obrigatório no ambiente.

## Consequências positivas

| Consequência | Efeito |
|---|---|
| Dev sem nuvem | MinIO local sobe com `make up` e não exige conta |
| Provedor trocável | Migrar de MinIO para S3 ou Supabase Storage não altera domínio |
| Banco enxuto | Backup e restore do PostgreSQL não carregam binário |
| URL assinada | Acesso temporário, revogável e auditável |
| Antivírus no caminho | Anexo só é aceito depois da verificação |
| Deploy horizontal | Qualquer réplica lê o mesmo objeto |

## Consequências negativas e trade-offs

| Trade-off | Custo aceito | Mitigação |
|---|---|---|
| Mais uma peça de infraestrutura | MinIO no compose, bucket em produção | Healthcheck e `make doctor` |
| Upload passa pela API | Consome banda e tempo do Django | Limite de 10 MB e processamento em streaming |
| URL assinada expira | Link compartilhado pode parar de funcionar | TTL de 5 min e regeneração sob demanda |
| Custo de armazenamento | PDFs e exports acumulam | Lifecycle de 7/90 dias e expurgo |
| Consistência entre banco e storage | Objeto órfão se a transação falhar | Gravação do objeto antes do commit + rotina de reconciliação |

## Alternativas descartadas

### Binário em `bytea` no PostgreSQL

Seria simples e transacional, mas infla o banco, torna o backup pesado e não escala para anexos de 10 MB. O PostgreSQL não é um CDN.

### Disco local da aplicação

Funciona em uma réplica só. Com duas réplicas, o arquivo gravado em uma não existe na outra; o deploy perde o conteúdo. Não atende ao RNF de disponibilidade.

### Upload direto do navegador para o storage

Reduziria a carga da API, mas transfere a validação de tipo e o antivírus para o cliente — que não é confiável. Se for adotado no futuro, exige URL pré-assinada de upload e um webhook de validação; fora do escopo do MVP.

### Bucket público para material de orientação

Simplificaria o cache e o CDN, mas impediria revogação e permitiria enumeração. O ganho não compensa o risco de expor um PDF com dado de outra pessoa por erro de chave.

### Provedor proprietário com SDK exclusivo

Amarra o projeto a um fornecedor e dificulta o desenvolvimento local. A API S3 é o denominador comum entre MinIO, AWS e Supabase Storage.

## Critérios de verificação

| Critério | Como verificar |
|---|---|
| MinIO sobe no ambiente local | `make up` e `mc ls local/sosp-private` |
| Upload rejeita arquivo acima de 10 MB | Teste de integração com arquivo de 11 MB |
| Upload rejeita extensão falsa | Arquivo `.pdf` que é executável; resposta `415` |
| URL assinada expira | Acessar o link após 301 s; resposta `403` |
| Nenhum bucket público | Inspeção da policy do bucket em staging |
| Nenhuma credencial no portal | Varredura por `AWS_SECRET` em `portal/` |
| PDF e export são gravados pelo worker | Teste de integração com storage fake |

## Referências

- [Pilar 3 — Arquitetura](../03-architecture.md)
- [Pilar 4 — Modelagem de Dados e Contratos de API](../04-data-api.md)
- [Pilar 5 — Engenharia, DevOps e Operação](../05-engineering-devops.md)
- [`.env.example`](../../.env.example)
- [ADR-005 — Processamento assíncrono e DLQ](ADR-005-processamento-assincrono-dlq.md)
