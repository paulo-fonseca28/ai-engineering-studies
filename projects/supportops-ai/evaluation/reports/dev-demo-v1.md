# Baseline dev / demo

Executado em 2026-10-29T16:59:12.820077+00:00. Casos: 21; repetições: 3.

| Métrica | Valor |
| --- | --- |
| executions | 63 |
| recall_at_1 | 0.5 |
| recall_at_3 | 0.5 |
| unanswerable_retrieval_rate | 0.6666666666666666 |
| latency_ms_median | 0.24 |
| latency_ms_p95 | 0.332 |

Valores nulos não foram medidos. Citações por ID não comprovam fidelidade semântica. Demonstração não mede qualidade de LLM.

## Falhas de recuperação (primeira repetição)

- dev-02: Quero pedir meu dinheiro de volta. (Recall@3=0.0)
- dev-04: Posso desistir da compra depois de começarem a cozinhar? (Recall@3=0.0)
- dev-06: Meu lanche está demorando demais para chegar. (Recall@3=0.0)
- dev-08: Veio apenas metade da refeição que comprei. (Recall@3=0.0)
- dev-10: Preciso trocar o local onde vou receber a comida. (Recall@3=0.0)
- dev-12: A mesma compra apareceu duas vezes na minha fatura. (Recall@3=0.0)
