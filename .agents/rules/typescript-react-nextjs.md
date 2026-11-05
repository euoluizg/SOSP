---
trigger: always_on
description: Convenções de engenharia para TypeScript, React e Next.js neste workspace.
---

- Preserve a arquitetura e as convenções já existentes.
- Use TypeScript com tipos explícitos nas fronteiras de sistema.
- Prefira componentes semanticamente corretos, acessíveis e focados.
- Em Next.js, prefira Server Components por padrão e Client Components somente quando necessários.
- Valide entradas no servidor e aplique autorização no servidor.
- Não exponha secrets nem dados privados ao bundle cliente.
- Trate estados de carregamento, vazio, erro e sucesso.
- Evite abstrações prematuras, duplicação e dependências desnecessárias.
- Consulte a documentação da versão instalada antes de usar APIs sensíveis à versão.
