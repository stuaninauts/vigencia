# Fontes e acesso testado

Testes feitos com curl em 2026-10-14. Reteste antes de construir em cima.

## Portal NF-e: Notas Técnicas (fonte principal)
- Lista: `https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=`
- Sem cookie, responde 302 para `?AspxAutoDetectCookieSupport=1`. Com cookie jar (`curl -c cj -b cj -L`) e
  User-Agent de navegador, responde 200 (~118 KB).
- ~320 links de documentos, de 2007 a 01/10/2026. **Versões antigas continuam listadas** (ex.: NT 2025.002 de
  v1.00, 28/03/2025, a v1.52, 01/10/2026: 15 versões).
- Download: `exibirArquivo.aspx?conteudo=<id>` devolve `application/pdf`. NT 2025.002 v1.52: 2,1 MB, 94 páginas.
- `pdftotext -layout` extrai bem: ~40 mil palavras, tabela "Histórico de Alterações / Cronograma" (implantação
  em homologação e em produção), tabelas de leiaute e anexos cClassTrib e cClassTribIS.
- A lista tem duas seções: "Documentos vigentes" (107) e "Documentos não vigentes" (213), em 2026-10-18. Só a
  última versão de cada NT fica em vigentes (NT 2025.002: v1.52 vigente, v1.00 a v1.51 não vigentes).
- Títulos trazem relações explícitas: "(substituída pela NT 2009.006)", prefixo "RT" (reforma tributária),
  "NFC-e", "Conjunta". O número não é chave: existem "NT 2025.001" e "NT Conjunta 2025.001".
- Sujeira real tratada em `src/vigencia/portal.py`: espaço não separável no título; o `+` do id em base64 aparece
  como espaço no HTML, inclusive no início (`" WTd7iuD21s="` é `+WTd7iuD21s=`).
- O portal aceita User-Agent que identifica o projeto (`vigencia/0.1 (+github...)`), sem fingir navegador.
- Corpus da fase 1 (`vigencia baixar`, padrão: vigentes publicados desde 2025-01-01): 24 documentos, 531 páginas, 22 MB.

## LC 214/2025 (Planalto)
- HTML no planalto.gov.br, respondeu 200 (~5,4 MB) num teste anterior. Não retestado.

## CGIBS: resoluções
- `https://www.cgibs.gov.br/resolucoes` responde 200, com PDFs em `/upload/arquivos/AAAAMM/`.
- A maioria das resoluções é administrativa (orçamento, regimento). Valor como corpus: baixo, exceto o regulamento do IBS.

## Calculadora RTC (piloto-cbs.tributos.gov.br)
- Qualquer caminho da API devolve a mesma página HTML de 5 KB com desafio anti-bot (F5, `/TSPD/`).
  Não é fonte automatizável. A tabela cClassTrib vem do anexo da própria NT.
