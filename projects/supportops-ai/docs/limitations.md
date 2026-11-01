# Limitações

- Corpus de seis políticas e perguntas sintéticas elaboradas pelo agente. Não há validação humana independente, generalização de domínio ou impacto de negócio medido.
- A versão grounded v3.2 preserva citações, mas respondeu com políticas irrelevantes em 2/6 perguntas sem resposta e não esclareceu 2/3 ambiguidades da bateria final. Consulte [resultados](../evaluation/RESULTS_V3.md).
- O limiar bloqueou duas perguntas respondíveis de desenvolvimento. Seus valores não se transferem automaticamente para outro modelo/corpus; o digest é validado.
- `needs_review` é constante no modo grounded; não mede uma competência do modelo. Citação literal não é validação semântica.
- O manifesto exclui documentos novos/adulterados. Não protege contra alguém que possa alterar código/manifesto nem contra aprovação equivocada de conteúdo malicioso. Os probes de integridade não são benchmark geral de prompt injection.
- O modo ollama mantém geração livre e erros observados nos [experimentos v1](../evaluation/RESULTS.md) e [v2](../evaluation/RESULTS_V2.md). Nenhuma ação externa é executada em qualquer modo.
- Todos os conjuntos publicados já estão expostos. São úteis como regressão, não como teste cego para ajustes posteriores. Repetições não aumentam o número de perguntas independentes.
- Temperatura zero/seed fixa não garantem determinismo entre versões/hardware. Latências incluem recusas e aquecimento; não representam produção. Tokens de embeddings e custo financeiro não são contabilizados.
- API local sem autenticação, persistência de rastros ou controle de concorrência. `/health` não verifica os modelos.
- Dependências verificadas em Python 3.12. Docker, CI remoto, deploy público da aplicação, pedidos, agentes com ferramentas e n8n permanecem pendentes.
