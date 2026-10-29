# Retrieval comparison — development

| Strategy | Recall@1 | Recall@3 | Retrieval on unanswerable | Median ms | p95 ms |
| --- | --- | --- | --- | --- | --- |
| lexical | 0.500 | 0.500 | 0.667 | 0.14 | 0.22 |
| semantic | 1.000 | 1.000 | 1.000 | 15.00 | 23.42 |
| hybrid | 0.917 | 1.000 | 1.000 | 14.22 | 23.27 |

Dense retrieval has no rejection threshold: it always returns top-k when the corpus is nonempty. This is not evidence sufficiency. First dense query includes initialization; document vectors are reused in memory. Query vectors are computed per search. No generation or semantic correctness is measured here.
