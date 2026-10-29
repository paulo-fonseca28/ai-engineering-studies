# Recuperação e fidelidade — v2

Experimentos de desenvolvimento executados em 29/10/2026. Implementação e configuração de geração congeladas em `73af2d7`; o comparador foi executado imediatamente antes desse commit e registra o HEAD anterior mais os hashes dos arquivos executados. Os relatórios v1 permanecem preservados. Não houve nova avaliação independente em teste nesta etapa.

## Recuperação

21 perguntas de desenvolvimento, três repetições por estratégia, seis políticas: 189 buscas, das quais 36 por estratégia são repetições das mesmas 12 perguntas respondíveis. Qwen3 Embedding 0.6B, digest e quantização registrados nos rastros. A instrução é aplicada à consulta, e os documentos semânticos incluem título e conteúdo; o lexical usa conteúdo. A comparação não isola apenas o efeito do modelo.

| Estratégia | Recall@1 | Recall@3 | Retorna algo nos casos sem resposta | Mediana da busca |
| --- | --- | --- | --- | --- |
| Lexical | 50,0% (6/12) | 50,0% (6/12) | 2/3 | 0,14 ms |
| Semântica | 100% (12/12) | 100% (12/12) | 3/3 | 15,00 ms |
| Híbrida RRF | 91,7% (11/12) | 100% (12/12) | 3/3 | 14,22 ms |

A primeira busca semântica levou 6,744 s, incluindo inicialização. As duas estratégias densas compartilham cache de documentos; consultas são calculadas por busca. A diferença de latência entre elas não sustenta uma conclusão de superioridade. Sem limiar de rejeição, top-k sempre retorna documentos. Similaridade não é suficiência de evidência.

Selecionamos semântica para o experimento seguinte pelo Recall@1 em desenvolvimento. A busca lexical continua sendo o padrão que funciona sem serviço de modelos.

## Geração com a estratégia selecionada

63 chamadas reais ao Qwen3 1.7B, mantendo o prompt v1 e os parâmetros de geração. Todas passaram pelo contrato, mas isso não garante fidelidade. Recall dos documentos esperados nas citações: 91,7%, menor que os 100% de recuperação. Mediana do fluxo: 748,424 ms; p95: 1.129,059 ms. Foram observados 52.659 tokens de entrada e 5.983 de saída do gerador; tokens de embeddings ainda não são contabilizados.

A pergunta sobre refeição incompleta recuperou a política correta, mas o modelo ainda respondeu em termos de cobrança duplicada/reembolso. Em pergunta sobre distância entre planetas, o modelo usou conhecimento externo e citou a política de itens faltando. Também permaneceu a afirmação indevida de cancelamento autorizado em um ataque. A recuperação melhorou; a geração não está pronta para uso autônomo.

## Revisão de fidelidade

O agente de desenvolvimento anotou todos os 21 casos da primeira repetição de cada relatório, mantendo perguntas, respostas, fontes, textos de referência, hash de origem e justificativa. **Revisão assistida por IA, sem validação humana independente**. São anotações descritivas de desenvolvimento, não uma estimativa de acurácia generalizável. As demais repetições não receberam rótulos de fidelidade.

| Veredito | Lexical v1 | Semântica v2 |
| --- | --- | --- |
| Sustentada e adequada (`supported`) | 8 | 9 |
| Afirmação não sustentada/contraditória (`unsupported`) | 3 | 5 |
| Incompleta, pouco esclarecedora ou com atribuição insuficiente (`incomplete`) | 3 | 7 |
| Abstenção sem resposta (`abstained`) | 7 | 0 |

A redução das abstenções veio acompanhada de mais respostas não sustentadas ou incompletas. Nenhum resultado desta revisão justifica liberar respostas automaticamente. Algumas anotações exigem julgamento, como decidir se a omissão de um identificador torna a resposta incompleta; as justificativas permitem revisão e contestação por uma pessoa.

## Evidências

- [Comparação de recuperação](reports/dev-retrieval-v2.md) · [JSON](reports/dev-retrieval-v2.json)
- [Geração semântica](reports/dev-semantic-ollama-v2.md) · [JSON](reports/dev-semantic-ollama-v2.json)
- [Revisão lexical](reports/dev-lexical-review-v1.json) · [Revisão semântica](reports/dev-semantic-review-v2.json)
- [Verificação HTTP](reports/http-retrieval-v2.json): semântica real, híbrida demonstrativa e modelo de embeddings ausente; neste último caso, revisão explícita, sem fontes nem chamada de geração.

36 testes automatizados passaram. Os testes cobrem vetores inválidos, dimensões, ranking, invalidação de cache, RRF, indisponibilidade do provedor e separação entre anotação de IA e validação humana.

## Decisão e próximos experimentos

Manter as estratégias configuráveis e o padrão lexical offline. Priorizar rejeição de evidência insuficiente, respostas fundamentadas nas afirmações citadas e esclarecimento de ambiguidades antes de integrações externas. Calibrar qualquer limiar apenas em desenvolvimento. Depois de congelar a configuração, avaliar um novo conjunto reservado; o teste v1 já foi exposto. Ataques em documentos recuperados, revisão humana e comparação de geradores continuam pendentes.
