# Golden set

Uma pergunta por linha em `perguntas.jsonl`, nos splits `dev` (livre para ajustar o sistema) e `test` (protegido:
só o humano lê e escreve; ver `AGENTS.md`).

| Campo | Conteúdo |
|---|---|
| `id` | `<tipo>-NN`, estável: resultados de experimentos referenciam este id |
| `origem` | `real` (como quem trabalha com NF-e pergunta) ou `sintetica` (só para garantir cobertura de um tipo) |
| `persona` | quem pergunta: `dev de ERP`, `suporte` ou `analista fiscal`; `null` nas sintéticas |
| `tipo` | tipo de pergunta do glossário: consulta de campo, regra de validação, temporal, diff, agregada, multi-hop, sem resposta |
| `pergunta` | no fraseado da persona: mensagem de rejeição colada sem acento, data concreta, contexto da operação |
| `resposta_esperada` | fatos que a resposta precisa conter, com IDs e datas literais |
| `citacoes` | `[{chave, versao, pagina}]` que sustentam a resposta; vazio em `agregada`; opcional em `sem resposta` (o trecho que mostra que a resposta não está lá) |
| `inspiracao` | link para a dúvida real que inspirou a pergunta, ou `null`; a pergunta é reescrita, nunca copiada |
| `notas` | por que a pergunta é difícil, de onde vem a resposta |
| `revisado` | `true` só depois de o humano conferir a resposta no PDF |

## Como as respostas são conferidas
Cada resposta esperada foi conferida na página renderizada do PDF, não só no texto extraído: as NTs riscam datas
substituídas e realçam o que mudou (verde na versão atual, amarelo na anterior), e o `pdftotext` perde as duas coisas.

## Composição do split `dev`
20 perguntas: 15 reais (dúvidas de dev de ERP, suporte e analista fiscal, várias a partir de rejeições) e 5 sintéticas
para cobrir tipos que as reais não cobrem bem.

Retrieval acerta uma pergunta quando algum chunk do top-k é da mesma NT e versão e cobre uma das páginas citadas.
