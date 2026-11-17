# Cancelamento com confirmação em simulação

API 0.6. Somente dados fictícios, sem modelos ou serviços externos envolvidos. O operador revisa uma proposta antes de enviar a confirmação. A API não comprova identidade nem revisão humana: confirmed=true é uma declaração do cliente. Use localmente, sem pedidos reais.

## Executar

Inicie a API conforme o README. Abra http://127.0.0.1:8000 para usar a interface local. Consulte o ID, prepare uma proposta, revise os estados e marque a confirmação antes de executar. Também é possível usar /docs ou os comandos abaixo:

```bash
curl -s http://127.0.0.1:8000/simulation/orders/DEMO-1001
curl -s http://127.0.0.1:8000/simulation/cancellations/proposals -H 'Content-Type: application/json' -d '{"order_id":"DEMO-1001"}'
```

Revise order_id, current_status, proposed_status e expires_at. Copie o proposal_id retornado para a confirmação:

```bash
curl -s http://127.0.0.1:8000/simulation/cancellations/confirmations -H 'Content-Type: application/json' -d '{"proposal_id":"SUBSTITUA_PELO_ID_DA_PROPOSTA","confirmed":true,"idempotency_key":"cancelamento-demo-0001"}'
curl -s http://127.0.0.1:8000/simulation/orders/DEMO-1001
```

Repita exatamente a confirmação para recuperar o mesmo resultado. A chave deve ter 8–128 caracteres ASCII alfanuméricos, hífen ou sublinhado. Outra proposta exige outra chave. O contrato de entrada está no OpenAPI /docs; campos extras, coerção de booleanos e IDs inválidos são rejeitados.

## Transições e garantias locais

- Somente received pode propor e confirmar cancelled; preparar, entregar e estados terminais retornam 409. Não há reembolso nem transições automáticas.
- Propor retorna 201 e grava uma proposta, sem mudar o pedido. A proposta expira após 300 segundos, inclusive no instante limite.
- Confirmar exige confirmed=true, proposta existente, não consumida, não expirada e a mesma versão/estado do pedido. Sucesso retorna 200; ausências 404, conflitos 409, entrada inválida 422, armazenamento indisponível 503.
- SQLite usa BEGIN IMMEDIATE. Alteração do pedido, consumo da proposta e resultado de execução são confirmados na mesma transação. Falha reverte todos. Cada execução possui execution_id e executed_at persistidos.
- Repetir a mesma chave/proposta devolve o resultado original, mesmo após expiração. mutations_executed=1 descreve a execução original, não uma nova alteração por repetição. Reutilizar chave para outra proposta ou confirmar a mesma proposta com outra chave retorna 409.

## Persistência e separação dos dados

O banco é criado e populado uma única vez a partir da fixture validada, no primeiro acesso a /simulation (inclusive GET). Caminho padrão: var/actions.sqlite3, relativo à pasta do projeto. SUPPORTOPS_ACTION_DB permite um caminho alternativo. Reiniciar o processo preserva os dados; editar a fixture não repopula bancos existentes. Para outra demonstração, use um caminho de banco novo. Arquivos locais de banco não são versionados.

GET /simulation/orders/{id} lê o estado mutável da simulação, com versão. GET /orders/{id} e POST /tickets continuam consultando o snapshot estático de orders.json. Esses universos são deliberadamente separados: uma simulação cancelada não altera o snapshot. A simulação não é invocada pelo modelo nem pelo fluxo de tickets. A interface na raiz da API usa exclusivamente /simulation. Em falhas de rede, uma nova tentativa na mesma tela preserva proposta e chave. Recarregar a página perde esse contexto; consulte o estado antes de iniciar outra operação. Descartar na tela não revoga a proposta no servidor: ela expira após cinco minutos.

SQLite serializa escritores; este contrato não promete coordenação entre bancos distintos nem execução exatamente uma vez em serviços externos. Não há autenticação, autorização, retenção/limpeza de propostas, migrações, auditoria de identidade ou backup gerenciado. Propostas expiradas permanecem armazenadas. A regra é fixa no código, não inferida da política pelo LLM.

## Validação

91 testes passaram em 17/11/2026 (10 novos). Incluem oito confirmações concorrentes com uma só execução, persistência ao reabrir o banco, isolamento da fixture, expiração, proposta desatualizada, conflito de chave, rollback após falha forçada e contratos ASGI. Testes usam bancos temporários. Não houve nova avaliação de modelos; as limitações de relevância anteriores permanecem.

Interface v0.7: um teste JavaScript do fluxo com DOM/fetch simulados passou, além dos 91 testes Python e checks HTTP reais da página e script. A renderização visual em navegador ainda não foi validada.
