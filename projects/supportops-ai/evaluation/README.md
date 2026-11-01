# Avaliação reproduzível

Políticas e perguntas são sintéticas, elaboradas pelo agente de desenvolvimento sem anotação humana independente. Dados de exemplo sob CC0-1.0. Cada pergunta tem ID, categoria e documentos de referência. A API e os experimentos usam o mesmo núcleo.

## Conjuntos e exposição

| Arquivo | Casos | Uso ocorrido |
| --- | --- | --- |
| dev.jsonl | 21: 12 respondíveis, 3 ambíguos, 3 sem resposta, 3 adversariais | Desenvolvimento, diagnóstico e calibração. |
| test.jsonl | 21, mesma composição | Baseline v1; exposto, agora regressão. |
| heldout-v3.jsonl | 24: 12 respondíveis, 6 sem resposta, 3 ambíguos, 3 adversariais | Primeira tentativa grounded v3; exposto. |
| heldout-v4.jsonl | 24, mesma composição | Contrato v3.1; exposto. |
| heldout-v5.jsonl | 24, mesma composição | Configuração final v3.2, congelado antes da execução; agora exposto. |

Não há perguntas exatamente iguais entre partições, mas existem paráfrases das mesmas seis políticas. Nenhum conjunto publicado deve ser tratado como teste cego para novos ajustes. As três repetições de cada pergunta medem variação de execução; não são três exemplos independentes.

## Comandos

Na pasta do projeto, com Ollama/modelos disponíveis para inferência real:

```bash
.venv/bin/python -m evaluation.run --split dev --mode demo --repeats 3 --output evaluation/reports/local-demo.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --strategy semantic --mode grounded --repeats 3 --output evaluation/reports/local-grounded.json
.venv/bin/python -m evaluation.compare --repeats 3 --output evaluation/reports/local-retrieval.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.verify_runtime --output evaluation/reports/local-runtime.json
```

Saídas existentes não são sobrescritas. Falha de recuperação/configuração invalida o experimento com saída não zero, preservando o relatório quando possível. Ausência total de inferência bem-sucedida também falha. Falhas parciais permanecem nas métricas. Não há fallback silencioso para demonstração.

O JSON registra respostas individuais, hashes do código/dados/prompts/manifesto, commit, ambiente, modelo, digest, opções e tokens retornados. O Markdown resume. Para reproduzir um relatório histórico, use seu commit e hashes, não presuma que o código atual corresponde a ele. Os tokens registrados são do chat/seletor, não dos embeddings; custo financeiro e validação semântica permanecem não medidos.

## Calibração e protocolo grounded

`python -m evaluation.calibrate --report evaluation/reports/dev-retrieval-v2.json --output evaluation/reports/local-threshold.json` aceita apenas resultados de desenvolvimento. Usa a primeira repetição semântica, uma grade declarada e a regra: rejeitar todos os casos sem resposta no desenvolvimento, maximizar retenção dos respondíveis e escolher o menor limiar em caso de empate. O limiar 0,47 preservou 10/12 respondíveis e rejeitou 3/3 sem resposta. Essa separação não foi garantida em novas perguntas.

O modo grounded verifica o manifesto antes de recuperar fontes, aplica o limiar ao cosseno e usa um seletor com referências curtas. Não aplica 0,47 a scores lexicais ou RRF. O renderizador devolve citação integral ou mensagem fixa; revisão é obrigatória por código. As fontes medidas pelo runner são as admitidas após o limiar.

## Métricas e limites

- Recall@1/@3: média da fração de documentos relevantes encontrados, apenas nos casos respondíveis.
- Recuperação em casos sem resposta: fração desses casos que ainda têm fonte após os filtros; não significa resposta correta.
- Aceitação do contrato: respostas estruturalmente aceitas sobre chamadas realmente tentadas. Falhas técnicas ficam no denominador; recusas antes de chamar o modelo não contam como inferência.
- Citação do documento esperado: cobertura documental, sem prova de adequação semântica.
- Integridade literal: compara a saída com o fragmento citado integralmente. É propriedade do renderizador, não acurácia geral.
- Respondíveis com documento esperado citado: cobertura útil após seleção, incluindo recusas/falhas como ausência de citação.
- Sem resposta sem citação: inclui esclarecimentos, recusas e falhas; não chamar automaticamente de abstenção correta.
- Ambiguidades esclarecidas: fração em que o modelo pediu esclarecimento; não mede a qualidade dessa pergunta.
- Citações em casos adversariais: contagem descritiva, não taxa de ataque bem-sucedido. É necessário ler o texto.
- Mediana/p95 nearest-rank: duração do fluxo, incluindo ingestão, busca e eventual seleção. Pode incluir carregamento; recusas sem seleção também estão no conjunto.

`needs_review=true` é constante no grounded e não mede comportamento aprendido. A verificação de corpus cobre exclusão de documento novo/alterado, não conteúdo malicioso que foi aprovado no manifesto. Prompt, schema e hashes não provam defesa geral contra ataques.

## Revisão de fidelidade

```bash
.venv/bin/python -m evaluation.review --report evaluation/reports/dev-semantic-ollama-v2.json --output evaluation/reports/local-review.json
.venv/bin/python -m evaluation.review --summarize evaluation/reports/local-review.json
```

A ficha traz todos os casos da primeira repetição, resposta, fontes recuperadas, políticas de referência e hash do relatório original. Começa como `pending`; não há aprovação automática. Cada anotação precisa de justificativa e tipo de revisor. `supported`, `unsupported`, `incomplete` e `abstained` separam sustentação, contradição, incompletude e ausência de resposta. Anotações `ai_assisted` não equivalem a validação humana independente.

## Relatórios consolidados

[Baseline v1](RESULTS.md) · [Busca e fidelidade v2](RESULTS_V2.md) · [Seleção restrita v3.2 e tentativas anteriores](RESULTS_V3.md)
