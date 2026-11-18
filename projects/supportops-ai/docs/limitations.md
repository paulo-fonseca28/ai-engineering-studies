# Limitações conhecidas

- Operação e dados inteiramente sintéticos. Sem clientes reais, validação humana independente, adoção ou impacto de negócio medido.
- O seletor grounded v3.2 preserva a citação, mas ainda pode escolher política irrelevante. Na avaliação final anterior, errou 2/6 casos sem resposta e não esclareceu 2/3 ambiguidades. `needs_review` é obrigatório, não uma habilidade do modelo. Os novos checks de integração não resolvem nem ocultam esses erros.
- Todos os conjuntos de avaliação publicados estão expostos. São regressão, não teste cego para novos ajustes. O limiar e o digest são específicos do corpus/modelo calibrados.
- Geração livre em ollama é experimental. A interface deve usar demo ou grounded para combinar pedido e política.
- Orquestração determinística com estado e ferramentas delimitadas; não há planejador autônomo, múltiplos agentes ou ferramentas de alteração acessíveis ao LLM.
- Token compartilhado identifica acesso ao ambiente, não uma pessoa. Não há contas, permissões por pedido, comprovação de revisão humana, limitação de requisições ou operação multi-inquilino. A configuração não é uma certificação para produção.
- SQLite local serializa escritores. A garantia de idempotência é por banco; não é uma transação distribuída. Reenvios concorrentes de atendimento podem repetir inferência antes de persistir o recibo vencedor. O sistema externo de teste deduplica separadamente.
- A fila de revisão registra pendências locais e mostra até 100 recentes. Não notifica pessoas, não oferece SLA nem substitui uma plataforma de atendimento. Não há reembolso ou integração com pedidos reais.
- O snapshot estático e a simulação são fontes distintas, indicadas no contrato. A interface usa a simulação. Rastros persistidos descrevem o momento original, não o estado mais recente.
- Propostas expiram em cinco minutos. Descartar na tela não revoga a proposta no servidor; recarregar perde o contexto da repetição. Consultar o estado antes de iniciar outra operação. Registros não são removidos automaticamente; backup e retenção são responsabilidade do operador.
- O workflow foi preparado para um sistema HTTP externo de teste configurável. Isso não equivale a integração com um SaaS de produção. Segredos ficam fora dos arquivos exportados.
- Latências de demonstração não são benchmarks de produção. Tokens reportados são do gerador; embeddings não entram na contagem. Não há custo financeiro de API pago nas execuções locais.
- O manifesto protege contra alterações não aprovadas no corpus, mas não contra alguém capaz de modificar código/manifesto. Probes de integridade não são um benchmark geral de prompt injection.

O estado de CI, Docker e hospedagem está registrado em [RELEASE.md](RELEASE.md), separado das capacidades implementadas.
