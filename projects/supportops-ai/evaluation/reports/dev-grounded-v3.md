# Evaluation dev / grounded / semantic

Executado em 2026-10-31T22:08:10.374573+00:00. Casos: 21; repetições: 3.

| Métrica | Valor |
| --- | --- |
| executions | 63 |
| recall_at_1 | 0.8333333333333334 |
| recall_at_3 | 0.8333333333333334 |
| unanswerable_retrieval_rate | 0 |
| latency_ms_median | 307.495 |
| latency_ms_p95 | 401.069 |
| llm.attempted | 48 |
| llm.completed | 27 |
| llm.contract_acceptance_rate | 0.5625 |
| llm.required_review_rate | 1 |
| llm.citation_document_recall | 0.6666666666666666 |
| llm.semantic_correctness | None |
| llm.task_success | None |
| llm.cost_usd | None |
| llm.input_tokens_observed | 32208 |
| llm.input_tokens_missing_calls | 0 |
| llm.output_tokens_observed | 1446 |
| llm.output_tokens_missing_calls | 0 |
| grounded.policy_quotes | 24 |
| grounded.literal_quote_integrity_rate | 1 |
| grounded.correct_document_quote_rate_answerable | 0.6666666666666666 |
| grounded.unanswerable_no_quote_rate | 1 |
| grounded.clarification_rate_ambiguous | 0 |
| grounded.adversarial_quote_count | 0 |
| grounded.semantic_correctness | None |

Valores nulos não foram medidos. Citações por ID não comprovam fidelidade semântica. Demonstração não mede qualidade de LLM.

## Falhas de recuperação (primeira repetição)

- dev-04: Posso desistir da compra depois de começarem a cozinhar? (Recall@3=0.0)
- dev-08: Veio apenas metade da refeição que comprei. (Recall@3=0.0)
