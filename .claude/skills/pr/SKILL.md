---
name: pr
description: Open (or update) the pull request for the current branch against main, with a test gate first and an evidence-based description following .github/pull_request_template.md. Use when the user asks to open, create or update a PR.
argument-hint: "[--draft] [context, e.g. issue number or what to highlight]"
disable-model-invocation: true
allowed-tools: Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git branch *) Bash(git fetch *) Bash(make check) Bash(gh auth status *) Bash(gh pr list *) Bash(gh pr view *) Bash(gh pr create *) Bash(gh api -X PATCH 'repos/{owner}/{repo}/pulls/*)
---

# Pull Request com gate de testes

Abre um PR da branch atual para `main` ou atualiza o PR que já existe.
Argumentos: `$ARGUMENTS` (`--draft` abre como rascunho; o resto é contexto extra do autor).

## Estado atual

- Branch: !`git branch --show-current`
- Working tree:

!`git status --short`

- Commits em relação a `origin/main`:

!`git log --format='%h %s' origin/main..HEAD`

---

## 1. Validação inicial

Pare com a mensagem indicada se:
- a branch é `main` → `❌ Você está na main. Crie uma branch tipo/descricao.`
- há mudanças não commitadas → `❌ Há mudanças não commitadas. Faça commit antes de abrir o PR.`
- não há commits à frente de `origin/main` → `❌ Nada para abrir: a branch não tem commits novos.`
- o nome não segue `tipo/descricao` (feat, fix, docs, refactor, perf, test, build, ci, chore) → avise e pergunte se segue mesmo assim.

Conta do GitHub: rode `gh auth status` e confira que a conta ativa é a dona do repo. Se não for, pare e peça ao autor
para logar (`! gh auth login`).

## 2. Sincronizar

```bash
git fetch origin main
git diff --stat origin/main...HEAD
```

Leia o diff (`git diff origin/main...HEAD`), não só os títulos dos commits.

## 3. Gate de testes (sempre)

Informe `▶ Rodando o gate…` e rode `make check`. Guarde o resultado real: testes passados, avisos, "N/N ok" dos hooks.
Se mudou retrieval, chunking, prompts ou geração: o PR precisa citar o experimento em `docs/experiments/` com as
métricas antes e depois. Sem isso, pare e avise: `❌ Mudança de qualidade sem experimento registrado.`

Se algo falhar, pare: `❌ Gate falhou: <item>. PR cancelado.` e mostre o erro.

## 4. Push

```bash
git push -u origin <branch>
```

## 5. Descrição

Preencha `.github/pull_request_template.md` seção por seção:
- **Título:** Conventional Commits, `tipo(escopo opcional): resumo`, imperativo, até 72 caracteres.
- **Summary:** o resultado em 1 a 3 frases.
- **Type of change:** só o que se aplica, com `[x]`; apague o resto.
- **Changes:** bullets factuais por área.
- **Eval impact:** tabela antes/depois do experimento, ou "No quality-affecting change".
- **How has this been tested:** só o que rodou no passo 3, com o resultado. O que não rodou vai em "Not tested".
- **Risk and rollback:** risco honesto com o motivo; rollback concreto.
- **Checklist:** `[x]` só no que foi verificado de fato.
- Remova comentários `<!-- -->` e seções que não se aplicam. Inglês, tom objetivo, **sem travessão longo (em dash)**.
- Termine com `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

Salve o corpo num arquivo temporário (fora do repo).

## 6. Criar ou atualizar o PR

```bash
gh pr list --head <branch> --state open --json number,url
```

- Já existe: `gh api -X PATCH 'repos/{owner}/{repo}/pulls/<número>' -f title="<título>" -F body=@<arquivo>`
- Não existe: `gh pr create --base main --head <branch> --title "<título>" --body-file <arquivo>` (+ `--draft` se pedido)

## 7. Resultado final

```
✅ PR CRIADO (ou ✅ PR ATUALIZADO)
  Branch : <branch> → main
  Gate   : make check ✅ (<N> testes · hooks N/N)
  URL    : <url>
```

## Notas

- **Não fazer merge.** O PR espera o CI verde. Merge só com pedido explícito do autor.
- Nunca force push.
