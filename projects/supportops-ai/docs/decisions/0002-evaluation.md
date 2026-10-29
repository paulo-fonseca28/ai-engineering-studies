# 0002 — Baseline auditável antes de busca semântica

Congelar um baseline lexical com seis políticas e duas partições de 21 casos. Registrar todas as execuções, inclusive falhas, e distinguir métricas de recuperação, aceitação do contrato e revisão solicitada. Correção semântica e sucesso de tarefa ficam sem valor até uma avaliação apropriada.

Usar Qwen3 1.7B local via Ollama no primeiro experimento, evitando pressupor orçamento de API. Prompt versionado, saída com JSON Schema, `think=false`, temperatura 0, seed 42 e limite de 512 tokens. Não há seleção de modelo baseada no teste.

Os relatórios identificam o digest do modelo, versão do runtime, hashes do código/prompt/dados e revisões Git. Relatórios não são sobrescritos. Falhas técnicas permanecem no denominador das tentativas; ausência de fontes não conta como chamada de modelo.

Documentação primária: [chat](https://docs.ollama.com/api/chat), [instalação](https://docs.ollama.com/linux), [modelo](https://ollama.com/library/qwen3:1.7b).
