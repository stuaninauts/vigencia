# 0003: Harness de desenvolvimento e fluxo de trabalho

**Data:** 2026-10-14 · **Status:** aceita

## Contexto
O código vai ser escrito em grande parte por agentes de código. O harness precisa dar ao agente instruções claras,
um jeito único de verificar o próprio trabalho e limites que não dependam de ele lembrar das regras. Também precisa
proteger a integridade do benchmark: um agente que vê o split `test` do golden set contamina os números.

## Decisão
- **Instruções:** `AGENTS.md` é a fonte (padrão aberto, lido por Codex, Cursor, Copilot e outros). O `CLAUDE.md`
  importa o `AGENTS.md` (`@AGENTS.md`) e acrescenta só o que é do Claude Code.
- **Python:** uv (ambiente, `uv.lock`, Python 3.13), src layout, ruff (lint e formatação), mypy strict, pytest com
  markers `network`, `eval` e `slow`.
- **Verificação única:** `make check` (lint, formatação, tipos, testes rápidos, testes dos hooks). O CI roda o mesmo alvo.
- **Git hooks (framework pre-commit):** `no-commit-to-branch` na `main`, gitleaks, ruff, mypy, higiene de arquivos,
  bloqueio de travessão longo e validação de Conventional Commits no `commit-msg`. Ferramentas Python rodam via
  `uv run`, então a versão vem do `uv.lock`.
- **Guardrails do Claude Code** (`.claude/settings.json`): permissões `deny` para `.env`, `~/.ssh` e
  `evals/golden/test/`; hook `PreToolUse` contra comandos destrutivos, push na `main`, `--no-verify`, `pip install`,
  acesso ao split `test` do golden set e remoção de volumes do Docker; hook `PostToolUse` que formata o `.py` editado.
- **Fluxo:** GitHub Flow (branch `tipo/descricao`, PR, CI verde, merge commit), Conventional Commits em português,
  skill `/pr` com gate. Mesmo método usado na prática no repo do site.
- **GitHub:** CI com actions pinadas por SHA e `permissions: contents: read`; Dependabot para uv e actions com
  cooldown de 7 dias; templates de PR (com seção de impacto em avaliação) e de issue (experimento e bug).
- **Documentação:** ADRs em `docs/decisions/`, cards de experimento em `docs/experiments/`, pesquisa em `docs/research/`,
  glossário em `docs/glossario.md` (um termo por conceito).
- **Escrita:** regras de linguagem controlada inspiradas no ASD-STE100 (imperativo, uma instrução por frase, voz ativa,
  frases curtas, termos do glossário) só no texto que agente ou LLM executa: `AGENTS.md`, skills, prompts e mensagens
  de erro. O STE completo não foi adotado: vale só para inglês, os docs estão em português, o dicionário é protegido
  por direitos autorais e o vocabulário restrito atrapalha explicar trade-offs em ADRs e experimentos.

## Alternativas consideradas
- **Só `CLAUDE.md`:** prende o projeto a uma ferramenta. O suporte nativo do Claude Code ao `AGENTS.md` ainda tem
  relatos conflitantes, então o import é o caminho que funciona em qualquer versão.
- **lefthook (usado no site):** bom em projeto Node; aqui o framework pre-commit é o padrão do ecossistema Python
  e já está instalado.
- **pyright em vez de mypy:** depende de Node; mypy strict cobre o necessário.
- **Squash merge:** perde a granularidade dos commits.
- **Rebase merge:** histórico linear, mas perde o agrupamento por PR que o merge commit preserva.

## Consequências
- O primeiro commit precisa ir para a `main` antes de existir PR: o humano roda
  `SKIP=no-commit-to-branch git commit -m "chore: estrutura inicial do repositório"`.
- Hooks são guardrails, não fronteira de segurança. A proteção real vem do GitHub, configurada depois de criar o remoto:
  ruleset na `main` (PR obrigatório com 0 aprovações, status check `check`, sem force push e sem deleção), merge commit
  como único método, secret scanning com push protection, Dependabot alerts e private vulnerability reporting.
- Mudança de qualidade (retrieval, chunking, prompts, geração) sem experimento registrado é barrada pela skill `/pr`.
