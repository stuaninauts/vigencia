# Golden set

Uma pergunta por linha em `perguntas.jsonl`, nos splits `dev` (livre para ajustar o sistema) e `test` (protegido:
só o humano lê e escreve; ver `AGENTS.md`).

| Campo | Conteúdo |
|---|---|
| `id` | `<tipo>-NN`, estável: resultados de experimentos referenciam este id |
| `tipo` | tipo de pergunta do glossário: consulta de campo, regra de validação, temporal, diff, agregada, multi-hop, sem resposta |
| `pergunta` | como um dev de ERP perguntaria (paráfrase é bem-vinda) |
| `resposta_esperada` | fatos que a resposta precisa conter, com IDs e datas literais |
| `citacoes` | `[{chave, versao, pagina}]` que sustentam a resposta; vazio em `agregada` e `sem resposta` |
| `notas` | por que a pergunta é difícil, de onde vem a resposta |
| `revisado` | `true` só depois de o humano conferir a resposta no PDF |

Retrieval acerta uma pergunta quando algum chunk do top-k é da mesma NT e versão e cobre uma das páginas citadas.
