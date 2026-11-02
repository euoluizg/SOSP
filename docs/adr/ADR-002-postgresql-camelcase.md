# ADR-002 — PostgreSQL 17 e convenção `camelCase` sem aspas

- **Status:** Aceito
- **Data:** 29/10/2026
- **Decisores:** Arthur Franco e Luiz Gustavo — CESMAC
- **Substitui:** —
- **Substituído por:** —

## Contexto

O projeto precisa de um banco relacional com integridade referencial, transações multi-entidade, busca textual em português e similaridade para tolerar erro de digitação. O catálogo é pequeno no início, mas a busca é o núcleo do RF-06: o cidadão digita "tirar rg" e precisa encontrar "Emitir Carteira de Identidade".

A disciplina adota uma convenção de nomenclatura em `camelCase` para tabelas e colunas, sem aspas duplas. A convenção entra em conflito direto com o comportamento do PostgreSQL: **identificadores não citados são dobrados para minúsculas**. `catalogService` é criado e consultado como `catalogservice`. Se o projeto usar aspas em algum ponto e não em outro, o mesmo nome lógico passa a referenciar dois objetos distintos.

O PostgreSQL 17 não possui `uuidv7()` nativo (a função chegou na versão 18). É preciso definir a estratégia de chave primária.

## Decisão

### Banco

Adotamos **PostgreSQL 17** como fonte única de verdade, com:

- `pg_trgm` para similaridade e busca tolerante a erro.
- Full-text search em português (`to_tsvector('portuguese', ...)`) em coluna gerada `searchVector` com índice GIN.
- Índices compostos para os filtros do RF-06 (categoria, órgão, canal, município).
- `numeric(10,2)` para custo, com constraint de faixa.
- `timestamptz` em todas as colunas temporais.
- Exclusão lógica via `isActive` e `deletedAt`, com índices únicos parciais.

**Onde roda:** desenvolvimento usa PostgreSQL 17 no Docker; staging e produção usam PostgreSQL 17 gerenciado no Supabase, na região `sa-east-1`. O Supabase entra **somente** como banco: Auth, Data API e Realtime ficam desabilitados, e o Django é a única porta de escrita. A decisão e as regras de conexão estão no [ADR-008](ADR-008-supabase-postgresql-gerenciado.md). O schema da aplicação fica em `public`.

### Nomenclatura

1. O nome **canônico** (documentação, código Python, TypeScript e conversas) é `camelCase` com prefixo do módulo: `catalogService`, `schedulingAppointment`, `accountsCitizen`.
2. O DDL e **todas** as queries são escritos **sem aspas duplas**. Exemplo: `SELECT userId, createdAt FROM userAccounts WHERE isActive = true;`.
3. Como o PostgreSQL dobra identificadores não citados, o nome **físico** no catálogo é a versão em minúsculas: `catalogservice`, `userid`, `createdat`.
4. **É proibido criar identificador com aspas.** Um identificador citado com maiúsculas cria um objeto distinto e quebra a resolução das queries sem aspas.
5. É proibido criar dois identificadores que só difiram por caixa (`userid` e `userId`). O CI verifica o catálogo e falha se encontrar qualquer identificador com maiúsculas — o que indica que foi criado com aspas.

### ORM

O Django sempre cita identificadores no SQL que gera. Para manter a coerência:

```python
class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=150)
    detailed_description = models.TextField(db_column="detailedDescription")
    is_free = models.BooleanField(default=False, db_column="isFree")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")

    class Meta:
        db_table = "catalogservice"          # nome físico, minúsculo
        indexes = [
            models.Index(fields=["name"], name="idxCatalogServiceName"),
        ]
```

O atributo Python permanece em `snake_case` (convenção do Django); o nome lógico em `camelCase` vive no `db_column` e na documentação. O `db_table` recebe o nome físico em minúsculas para que o SQL citado pelo Django resolva para o mesmo objeto das queries sem aspas.

### Chave primária

- **Agora:** `uuid` gerado por `gen_random_uuid()` (UUID v4), disponível nativamente desde o PostgreSQL 13.
- **Evolução:** quando o ambiente migrar para PostgreSQL 18, trocar o default para `uuidv7()`, que preserva ordenação temporal e melhora localidade de índice.
- **Fallback de aplicação:** se for necessário UUID v7 no PostgreSQL 17, gerar no Django com a biblioteca `uuid6` e gravar explicitamente.

## Consequências positivas

| Consequência | Efeito |
|---|---|
| Um único comportamento de resolução | DDL e queries sem aspas sempre apontam para o mesmo objeto |
| Sem surpresa de caixa | Nenhum `relation "UserAccounts" does not exist` |
| Busca robusta sem Elasticsearch | `pg_trgm` + full-text resolvem o RF-06 |
| Integridade referencial | FKs e constraints garantem agendamento e protocolo coerentes |
| Migração futura para UUID v7 | Default isolado, troca de uma linha |

## Consequências negativas e trade-offs

| Trade-off | Custo aceito | Mitigação |
|---|---|---|
| Nome físico não é visualmente `camelCase` | `\d catalogservice` mostra tudo minúsculo | Documentação e dicionário de dados usam o nome canônico |
| Django cita identificadores | `db_table` e `db_column` precisam do nome físico | Revisão de migrations + teste de schema |
| Sem `uuidv7()` no PG 17 | Índices menos localizados que UUID v7 | Monitorar bloat; migrar quando o ambiente permitir |
| Full-text não é semântico | Sinônimos precisam de tabela e curadoria | `searchSynonym` + log de busca sem resultado |

## Alternativas descartadas

### `snake_case` em todo o projeto

Seria a convenção mais natural para PostgreSQL e para o Django, e é o que o documento de arquitetura original usava (`catalog_service`). Foi descartada porque a convenção da disciplina exige `camelCase`. **Se a restrição acadêmica deixar de existir, esta é a alternativa recomendada**, com migração de nomes via `ALTER TABLE ... RENAME TO`.

### `camelCase` com aspas duplas

Funcionaria tecnicamente, mas contradiz a regra explícita do projeto e cria uma armadilha: qualquer query sem aspas — inclusive de ferramentas, ORMs e scripts de BI — falharia. Seria necessário citar todos os identificadores em todo lugar, para sempre.

### Banco NoSQL

Perderia integridade referencial, transações multi-entidade e a busca textual nativa. O domínio é relacional por natureza: cidadão, serviço, unidade, slot, agendamento e protocolo têm cardinalidades claras.

### Elasticsearch desde a v1

Adiciona um cluster, um pipeline de indexação e um ponto de falha para um catálogo que começa pequeno. O PostgreSQL resolve o MVP; o Elasticsearch entra se a relevância ou o volume exigirem.

## Critérios de verificação

| Critério | Como verificar |
|---|---|
| Nenhum identificador citado no banco | `SELECT ... FROM information_schema` filtrando `[A-Z]`; resultado deve ser vazio |
| DDL executa do zero | `psql -f docs/database/schema.sql` em banco limpo |
| Queries de exemplo funcionam sem aspas | Suíte de smoke SQL |
| `db_table` e `db_column` conferem | Teste que compara `information_schema` com os models |
| Busca usa índice | `EXPLAIN ANALYZE` com `Bitmap Index Scan` em `idxCatalogServiceSearchVector` |

### Query de verificação de identificadores

```sql
-- Deve retornar zero linhas. Qualquer linha indica identificador criado com aspas.
SELECT table_schema, table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (table_name ~ '[A-Z]' OR column_name ~ '[A-Z]');
```

## Referências

- [Pilar 4 — Modelagem de Dados e Contratos de API](../04-data-api.md)
- [schema.sql](../database/schema.sql)
- [ADR-008 — Supabase como PostgreSQL gerenciado](ADR-008-supabase-postgresql-gerenciado.md)
- Documentação PostgreSQL: identificadores e folding de caixa.
- Documentação PostgreSQL 18: `uuidv7()`.
