# Glossário

Um termo por conceito. Use o termo da coluna **Termo** em código, docs, prompts e golden set. Não use os termos da
coluna **Não usar**. Termo novo entra aqui antes de ser usado. Exemplos conferidos na NT 2025.002 v1.52.

## Domínio: NF-e e reforma tributária
| Termo | Definição | Não usar |
|---|---|---|
| **NT** (Nota Técnica) | Documento do Portal NF-e que altera leiaute, regras de validação ou eventos. Identificada por ano e número: `NT 2025.002`. | nota, norma, manual |
| **versão** | Cada publicação de uma NT: `NT 2025.002 v1.52`. Uma versão substitui a anterior da mesma NT. | revisão, edição, release |
| **Histórico de Alterações** | Tabela da NT com cada versão e suas datas de implantação. Nome na NT: "Histórico de Alterações / Cronograma". | changelog, cronograma (sozinho) |
| **homologação** | Ambiente de teste da SEFAZ (`tpAmb=2`). A NT também chama de "Teste" na coluna de implantação. | teste (sozinho), staging, sandbox |
| **produção** | Ambiente real da SEFAZ (`tpAmb=1`). | prod, ambiente real |
| **implantação** | Data em que uma mudança passa a valer num ambiente. Sempre com o ambiente: "implantação em homologação", "implantação em produção". | go-live, entrada em vigor |
| **vigente** | Definição do projeto: uma regra está vigente na data D no ambiente A se D é igual ou posterior à implantação em A, e nenhuma versão implantada em A até D a retirou ou alterou. | válida, ativa, em vigor |
| **leiaute** | Estrutura do XML definida nas tabelas da NT, com as colunas ID, Campo, Ele, Pai, Tipo, Ocor., Tam. e Descrição. | layout, formato |
| **schema** | Arquivo XSD que valida o XML. Não é o mesmo que leiaute. | leiaute (para o XSD) |
| **campo** | Linha do leiaute. Tem ID e nome: o campo `AR03` tem nome `tpAmb`, elemento `E`, pai `AR01`, tipo `N`, ocorrência `1-1`, tamanho `1`. | tag, atributo, elemento (sozinho) |
| **grupo** | Campo que agrupa outros campos: `W03` (Total da NF-e - IBS / CBS / IS). | seção, bloco |
| **regra de validação** | Verificação que a SEFAZ faz no XML. Tem ID (`UB01-10`), modelos (`55/65`), aplicação (`Obrig.`), código de rejeição e mensagem. | validação (sozinho), check, critério |
| **rejeição** | Resposta da SEFAZ quando uma regra de validação falha. Tem código e mensagem: `1011 Rejeição: Não é permitido uso do Imposto Seletivo...`. | erro, falha |
| **modelo** | Tipo de documento fiscal: `55` é NF-e, `65` é NFC-e. | tipo de nota |
| **evento** | Registro enviado à SEFAZ ligado a um documento fiscal já autorizado. | |
| **RTC** | Reforma Tributária do Consumo. A NT 2025.002 se chama "NT 2025.002-RTC". | reforma (sozinho, em código) |
| **IBS** | Imposto sobre Bens e Serviços. | |
| **CBS** | Contribuição Social sobre Bens e Serviços. | |
| **IS** | Imposto Seletivo. | |
| **LC 214** | Lei Complementar 214/2025, que institui IBS, CBS e IS. | lei da reforma |
| **CST** | Código de Situação Tributária. | |
| **cClassTrib** | Código de Classificação Tributária do IBS e da CBS (anexo III da NT 2025.002). Para o IS, `cClassTribIS` (anexo II). | classificação (sozinho) |

## Sistema
| Termo | Definição | Não usar |
|---|---|---|
| **documento** | Um arquivo de uma versão de NT (um PDF). Unidade de ingestão. | arquivo (para o conceito), fonte |
| **manifesto** | Registro de cada documento baixado: NT, versão, URL, hash, data de publicação e datas de implantação. | catálogo (para isso), índice de arquivos |
| **chunk** | Pedaço de documento indexado para busca, com metadados de NT, versão e implantação. | trecho, passagem, pedaço |
| **índice textual** | Onde ficam os chunks para busca lexical e vetorial (Postgres + pgvector). | vector store, base vetorial |
| **catálogo** | Tabelas estruturadas extraídas das NTs: campos, regras de validação, rejeições, implantações. | base estruturada, banco de regras |
| **busca lexical / vetorial / híbrida** | Métodos de retrieval: por termos (BM25), por embedding, ou os dois combinados. | keyword search, semantic search |
| **retrieval** | Etapa que escolhe os chunks ou registros do catálogo para responder. | recuperação, busca (para a etapa) |
| **roteador** | Componente que decide se a pergunta vai para o índice textual, o catálogo, o grafo ou uma combinação. | router, dispatcher |
| **citação** | Referência verificável na resposta: NT, versão, página e, se houver, ID da regra ou do campo. | fonte, referência (sozinho) |

## Avaliação
| Termo | Definição | Não usar |
|---|---|---|
| **golden set** | Conjunto versionado de perguntas com resposta esperada e citação esperada. | dataset de teste, gabarito |
| **split** | Divisão do golden set: `dev` (livre para ajustar) e `test` (só para o número final, protegido). | conjunto de validação |
| **tipo de pergunta** | Categoria da pergunta: consulta de campo, regra de validação, temporal, diff, agregada, multi-hop, sem resposta. | categoria, classe |
| **experimento** | Mudança de uma variável medida contra um baseline no mesmo golden set. Registrado em `docs/experiments/`. | teste (para isso), tentativa |
| **baseline** | Config de referência de um experimento. | padrão, controle |
| **variável** | A única coisa que muda entre baseline e variante. | parâmetro (para isso) |
