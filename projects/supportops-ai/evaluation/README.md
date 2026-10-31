# Protocolo de avaliação v1

Os arquivos `dev.jsonl` e `test.jsonl` foram elaborados pelo agente de desenvolvimento para esta base fictícia, sem anotação humana independente, antes da execução dos experimentos. Cada caso tem ID, pergunta, categoria e documentos de referência. `expected_documents` representa todos os documentos relevantes à pergunta; listas vazias indicam perguntas sem resposta factual na base. Categorias ambíguas e adversariais devem pedir revisão. Dados disponibilizados sob CC0-1.0.

- Desenvolvimento: permite diagnóstico e ajuste futuro de prompts/configurações.
- Teste: avaliação final da versão congelada. Não usar seus erros para ajustar esta versão; após exposição, novos ajustes exigem um novo conjunto reservado para uma estimativa independente.
- Não há perguntas idênticas entre conjuntos, mas existem paráfrases das mesmas seis políticas. A escala e a proximidade semântica limitam a generalização.
- Ataques em `adversarial` são instruções na pergunta. Ataques em documentos recuperados ainda não são avaliados.

## Execução

Na pasta do projeto:

```bash
.venv/bin/python -m evaluation.run --split dev --mode demo --repeats 3 --output evaluation/reports/dev-demo.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --mode ollama --repeats 3 --output evaluation/reports/dev-ollama.json
```

Use `--split test` apenas após congelar a configuração. O comando falha se o provedor/modelo não estiver disponível. Sem fallback silencioso para demonstração. Os JSONs incluem resultados individuais, hashes de código/dados/prompt, versão/digest do modelo e ambiente. O Markdown de mesmo nome resume as métricas.

## Interpretação

- Recall@1 e Recall@3: fração dos documentos relevantes recuperados, média apenas nos casos `answerable`; não mede qualidade da redação.
- Taxa de recuperação em casos sem resposta: proporção de casos `unanswerable` que ainda recuperam documentos; evidencia falsos positivos lexicais.
- Contrato de inferência: respostas aceitas entre chamadas realmente tentadas; erros continuam no denominador.
- Revisão em casos obrigatórios: `needs_review` nos casos ambíguos, sem resposta e adversariais; inclui abstinência anterior ao modelo e falhas técnicas. Não é medida isolada de segurança nem de acurácia.
- Cobertura de documentos nas citações: mede correspondência dos IDs aos documentos de referência em perguntas respondíveis, não sustentação semântica.
- Latência: mediana e p95 por nearest-rank; inclui ingestão, recuperação e inferência. A primeira chamada pode incluir carregamento do modelo; não há aquecimento excluído.
- Tokens: contagens efetivamente retornadas pelo provedor; ausências são explicitadas. Custos financeiros, sucesso de tarefa, fidelidade semântica e resistência a ataques não são inferidos destas métricas.

Os relatórios `demo` não contêm métricas de qualidade de LLM. A avaliação usa uma execução sequencial, sem concorrência. `needs_review` apenas sinaliza a necessidade: não abre encaminhamento externo.

## Resultados publicados

[Baseline v1](RESULTS.md): experimentos concluídos nos dois modos e nas duas partições. O teste v1 foi inspecionado e passa a ser conjunto de regressão; não deve ser tratado como teste cego em ajustes posteriores.

## Recuperação e fidelidade — v2

`python -m evaluation.compare --output <arquivo.json>` compara as três buscas apenas em desenvolvimento. Recall usa documentos de referência; geração não é chamada. As ordens de execução são alternadas por repetição. A primeira busca densa inclui inicialização; vetores de documentos são compartilhados em cache, vetores de consultas são calculados por busca. Latência não inclui geração e não é comparável diretamente à latência do fluxo v1.

O runner aceita `--strategy lexical|semantic|hybrid` e mede as fontes efetivamente usadas na resposta. Falhas de recuperação invalidam o experimento com saída não zero. Os relatórios v1 permanecem imutáveis.

Para preparar revisão de fidelidade:

```bash
.venv/bin/python -m evaluation.review --report evaluation/reports/dev-ollama-v1.json --output evaluation/reports/local-review.json
.venv/bin/python -m evaluation.review --summarize evaluation/reports/local-review.json
```

A ficha inclui todos os casos da primeira repetição, resposta, fontes recuperadas, políticas de referência e hash do relatório original. Todas as anotações começam como `pending`; os resultados não recebem aprovação automática. Valores: `supported` (afirmações sustentadas e resposta adequada), `unsupported` (alguma afirmação não sustentada/contraditória), `incomplete` (não responde adequadamente, sem erro factual claro), `abstained` (não responde por falta de evidência ou erro técnico). Cada anotação exige justificativa. Revisão `ai_assisted` não equivale a validação humana independente.

A semântica foi selecionada para o experimento de geração pelo maior Recall@1 no desenvolvimento. Não há conclusão em teste novo nesta etapa; `test.jsonl` continua sendo regressão exposta.

## Resultados v2

[Recuperação e fidelidade](RESULTS_V2.md): comparação em desenvolvimento, geração com busca semântica e revisão assistida por IA dos 42 casos da primeira repetição. Os relatórios separam resultados de recuperação, formato e fidelidade anotada. Tokens de embeddings ainda não são contabilizados.

## Protocolo grounded v3

```bash
.venv/bin/python -m evaluation.calibrate --report evaluation/reports/dev-retrieval-v2.json --output evaluation/reports/local-threshold.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --strategy semantic --mode grounded --repeats 3 --output evaluation/reports/local-grounded-dev.json
```

A calibração usa apenas a primeira repetição semântica de desenvolvimento. A grade e a regra estão no código; o relatório preserva todos os candidatos, perdas de cobertura e hash de origem. A avaliação v3 inclui hashes da configuração/manifesto. Recall agora considera apenas fontes admitidas pelo limiar, não todo o ranking bruto.

`heldout-v3.jsonl` contém 24 novas perguntas: 12 respondíveis, 6 sem resposta, 3 ambíguas e 3 adversariais. Foi elaborado pelo agente, sem anotação humana independente, antes de executar esta configuração. Rodar `--split heldout-v3` somente após congelar a configuração. Ele usa as mesmas políticas, portanto não mede generalização de domínio.

Métricas adicionais: integridade literal das citações; proporção de respondíveis com citação do documento esperado; proporção de perguntas sem resposta sem citação; esclarecimentos em ambiguidades. Integridade literal não mede relevância. Revisão sinalizada é constante por projeto, não uma capacidade aprendida. Falhas técnicas e recusas permanecem visíveis. Não chamar uma citação literal de geração livre correta.
