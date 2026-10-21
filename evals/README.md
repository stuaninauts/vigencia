# Avaliação

## Retrieval (sem custo)
`uv run vigencia avaliar-busca --config configs/<config>.toml`: recall@k e MRR no golden set, por origem e por tipo,
com latência p50 e p95. Não chama API.

## Ponta a ponta (busca, geração e juiz)
1. **Estimar:** `make eval` (ou `CONFIG=configs/<config>.toml make eval`) faz a busca de todas as perguntas e
   estima o custo da geração e do juiz. Não chama API.
2. **Rodar:** `make eval CONFIRMAR=1`. Gera a resposta com citação para cada pergunta, julga e grava a execução em
   `evals/execucoes/AAAAMMDD-HHMM-<config>.jsonl`, com resposta, citações, veredito, tokens, custo e latência.
   O hook do Claude Code sempre pede confirmação humana antes desse comando.
3. **Rotular:** `uv run vigencia rotular evals/execucoes/<execução>.jsonl` cria `evals/rotulos/<execução>.jsonl`.
   Um humano preenche `correta` e `fundamentada` (true ou false) lendo a resposta esperada e a do sistema. Os campos
   vêm vazios de propósito: o juiz não ancora o humano.
4. **Calibrar:** `uv run vigencia calibrar evals/execucoes/<execução>.jsonl evals/rotulos/<execução>.jsonl` mostra,
   por critério, a concordância, o kappa de Cohen e as perguntas em que juiz e humano divergiram.

## Critérios do juiz (`src/vigencia/juiz.py`)
Binários, com a crítica escrita antes da decisão:
- **correta:** traz os fatos essenciais da resposta esperada e não contradiz nenhum (datas, IDs, códigos e valores
  iguais). Em `sem resposta`, só é correta se disser que não encontrou.
- **fundamentada:** cada afirmação essencial tem citação, e o trecho citado a sustenta.
- **passa:** correta e fundamentada.

## Quando confiar no juiz
O juiz só substitui a leitura humana depois de calibrado: kappa de pelo menos 0,6 em cada critério, com cerca de
20 rótulos humanos. Abaixo disso, ajuste o prompt do juiz (não o sistema) e calibre de novo. Divergências são o
melhor material para entender o que o juiz não está vendo.

## Splits
- `golden/dev/`: livre para ajustar o sistema.
- `golden/test/`: protegido. Só o humano lê e escreve; o número final de um experimento sai de `make eval-test`.
