# Baseline dev / ollama

Executado em 2026-10-29T17:00:33.035631+00:00. Casos: 21; repetições: 3.

| Métrica | Valor |
| --- | --- |
| executions | 63 |
| recall_at_1 | 0.5 |
| recall_at_3 | 0.5 |
| unanswerable_retrieval_rate | 0.6666666666666666 |
| latency_ms_median | 536.338 |
| latency_ms_p95 | 1318.16 |
| llm.attempted | 42 |
| llm.completed | 42 |
| llm.contract_acceptance_rate | 1 |
| llm.required_review_rate | 1 |
| llm.citation_document_recall | 0.5 |
| llm.semantic_correctness | None |
| llm.task_success | None |
| llm.cost_usd | None |
| llm.input_tokens_observed | 28137 |
| llm.input_tokens_missing_calls | 0 |
| llm.output_tokens_observed | 3592 |
| llm.output_tokens_missing_calls | 0 |

Valores nulos não foram medidos. Citações por ID não comprovam fidelidade semântica. Demonstração não mede qualidade de LLM.

## Falhas de recuperação (primeira repetição)

- dev-02: Quero pedir meu dinheiro de volta. (Recall@3=0.0)
- dev-04: Posso desistir da compra depois de começarem a cozinhar? (Recall@3=0.0)
- dev-06: Meu lanche está demorando demais para chegar. (Recall@3=0.0)
- dev-08: Veio apenas metade da refeição que comprei. (Recall@3=0.0)
- dev-10: Preciso trocar o local onde vou receber a comida. (Recall@3=0.0)
- dev-12: A mesma compra apareceu duas vezes na minha fatura. (Recall@3=0.0)
