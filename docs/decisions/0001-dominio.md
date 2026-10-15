# 0001: Domínio do laboratório

**Data:** 2026-10-14 · **Status:** aceita

## Decisão
Documentação técnica da NF-e na reforma tributária do consumo (Notas Técnicas do Portal NF-e, com foco na
NT 2025.002 RTC), com a LC 214/2025 como base legal.

## Por quê
- **Versionamento real:** o portal mantém as versões antigas (15 versões da NT 2025.002 em 18 meses), o que
  sustenta ingestão incremental, diff e retirada de conteúdo do índice sem simulação.
- **Problemas difíceis de RAG no mesmo corpus:** tabelas que atravessam páginas, identificadores exatos,
  duas datas de vigência por regra, referências cruzadas e hierarquia de campos.
- **Contraparte estruturada natural:** leiautes e regras de validação viram tabelas consultáveis por SQL.
- **Respostas verificáveis sem ser especialista tributário:** as perguntas são sobre campos, regras e datas escritas
  literalmente no documento, não sobre interpretação da lei.
- **Fonte pública, em português, com publicação frequente** (5 NTs publicadas em 01/10/2026).

## Alternativas consideradas
- **Triagem de vulnerabilidades (CVE/SBOM):** dados excelentes (NVD, OSV, KEV, EPSS) e rejeição de CVEs em escala,
  mas tema mais explorado e corpus em inglês.
- **Normas do Banco Central (Pix e meios de pagamento):** API com versão, revogação e normas vinculadas, mas API não
  documentada e menos estrutura tabular.
- Outros avaliados e descartados por acesso, licença ou falta de atualização contínua: reguladoras (ANS, ANEEL),
  ZARC, Câmara, PNCP, CVM, clima espacial, regras de jogos, F1.

## Riscos
- Portal NF-e exige cookie e User-Agent de navegador; mudanças no portal podem quebrar o crawler.
- API da calculadora RTC fica atrás de anti-bot; não é fonte automatizável.
- Escopo tributário é grande: manter o recorte inicial (ver `docs/visao-macro.md`).
