# Baseline test / ollama

Executado em 2026-10-29T17:01:36.941200+00:00. Casos: 21; repetições: 3.

| Métrica | Valor |
| --- | --- |
| executions | 63 |
| recall_at_1 | 0.5833333333333334 |
| recall_at_3 | 0.6666666666666666 |
| unanswerable_retrieval_rate | 0.6666666666666666 |
| latency_ms_median | 518.042 |
| latency_ms_p95 | 960.52 |
| llm.attempted | 54 |
| llm.completed | 54 |
| llm.contract_acceptance_rate | 1 |
| llm.required_review_rate | 1 |
| llm.citation_document_recall | 0.6666666666666666 |
| llm.semantic_correctness | None |
| llm.task_success | None |
| llm.cost_usd | None |
| llm.input_tokens_observed | 34344 |
| llm.input_tokens_missing_calls | 0 |
| llm.output_tokens_observed | 4166 |
| llm.output_tokens_missing_calls | 0 |

Valores nulos não foram medidos. Citações por ID não comprovam fidelidade semântica. Demonstração não mede qualidade de LLM.

## Falhas de recuperação (primeira repetição)

- test-02: Vocês garantem quanto vou receber de volta? (Recall@3=0.0)
- test-08: A sacola chegou sem a sobremesa. (Recall@3=0.0)
- test-10: Mudei de lugar e preciso redirecionar a refeição. (Recall@3=0.0)
- test-12: Debitaram duas vezes o valor da mesma compra. (Recall@3=0.0)
