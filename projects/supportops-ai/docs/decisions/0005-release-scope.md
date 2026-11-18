# ADR 0005 — Fechar uma aplicação local verificável

## Decisão

A versão 1.0 integra atendimento, estado simulado, evidências, revisão confirmada, cancelamento e automação HTTP de teste. Mantém SQLite para persistência e busca vetorial em memória. Não adiciona PostgreSQL/pgvector ou múltiplos agentes sem necessidade medida. Testes existentes usam unittest; não migramos para pytest apenas para trocar a ferramenta.

O roteamento é explícito: policy, order_status ou order_policy, com snapshot ou simulation. O modelo escolhe somente a referência de uma política aprovada; não decide IDs, autorização, elegibilidade ou execução. Cancelamentos são uma transição codificada received → cancelled com proposta, validade e confirmação. Encaminhamentos são registros locais confirmados, sem envio de mensagens.

A API mantém o padrão snapshot para compatibilidade; a interface usa simulation explicitamente. Um atendimento persistido é evidência histórica, não uma consulta viva.

## Consequências

A demonstração é reproduzível sem modelos; grounded permite inferência real e mantém os limites da avaliação anterior. Há menos infraestrutura para executar e explicar. Escalabilidade multiusuário, armazenamento vetorial dedicado, autorização por cliente e efeitos externos reais exigiriam novo desenho e não são alegados nesta entrega.

CI e imagem de contêiner verificam empacotamento; hospedagem pública depende de destino e recursos próprios. Não assumir que uma aplicação testada localmente já está publicada como serviço.
