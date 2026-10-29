# Protocolo de avaliação v1

Os arquivos `dev.jsonl` e `test.jsonl` foram escritos manualmente para esta base fictícia, antes da execução dos experimentos. Cada caso tem ID, pergunta, categoria e documentos de referência. `expected_documents` representa todos os documentos relevantes à pergunta; listas vazias indicam perguntas sem resposta factual na base. Categorias ambíguas e adversariais devem pedir revisão. Dados disponibilizados sob CC0-1.0.

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
