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
- Atenção: alguns ids de conteúdo têm espaços no HTML; normalizar antes de montar a URL.

## LC 214/2025 (Planalto)
- HTML no planalto.gov.br, respondeu 200 (~5,4 MB) num teste anterior. Não retestado.

## CGIBS: resoluções
- `https://www.cgibs.gov.br/resolucoes` responde 200, com PDFs em `/upload/arquivos/AAAAMM/`.
- A maioria das resoluções é administrativa (orçamento, regimento). Valor como corpus: baixo, exceto o regulamento do IBS.

## Calculadora RTC (piloto-cbs.tributos.gov.br)
- Qualquer caminho da API devolve a mesma página HTML de 5 KB com desafio anti-bot (F5, `/TSPD/`).
  Não é fonte automatizável. A tabela cClassTrib vem do anexo da própria NT.
