# 0003 — Comparação de busca e revisão de fidelidade

Manter lexical como padrão offline. Oferecer semântica via Qwen3 Embedding 0.6B local e híbrida por Reciprocal Rank Fusion (soma de `1 / (60 + posição)` nas listas completas). O baseline lexical não muda. A busca semântica usa títulos e conteúdo; lexical continua usando conteúdo. Portanto a comparação avalia estratégias completas, não isola exclusivamente o efeito do embedding.

Aplicar a instrução de recuperação somente à consulta. Normalizar vetores e usar produto interno como cosseno. Validar dimensão, quantidade, valores finitos e norma. Cache limitado a oito entradas por processo, com conteúdo, digest e endpoint na chave. Não modificar o modelo/tag durante um experimento; resolução e inferência não são uma transação atômica.

Sem limiar de rejeição nesta versão: vizinhos próximos não garantem resposta sustentada. Falha do provedor fica explícita. Qwen3 Embedding 0.6B é um candidato inicial, não a melhor opção presumida.

Selecionar semântica para estudar geração porque obteve maior Recall@1 no desenvolvimento (12/12 contra 11/12 híbrido). Não selecionar com o teste v1, já exposto. Revisar afirmações ao lado de políticas, sem confundir aprovação do JSON com fidelidade.

Fontes: [API de embeddings](https://docs.ollama.com/api/embed), [modelo e instruções](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), [distribuição Ollama](https://ollama.com/library/qwen3-embedding:0.6b).
