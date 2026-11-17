# Consulta de pedidos sintéticos

A versão 0.5 adiciona `lookup_order`, ferramenta somente leitura com entrada e saída Pydantic estritas. [Contrato JSON Schema](lookup-order.schema.json). Os cinco pedidos DEMO-1001 a DEMO-1005 representam recebido, em preparo, em entrega, entregue e cancelado. Os valores e estados são fictícios, em um snapshot fixo de 17/11/2026, sem atualização em tempo real.

```bash
curl -s http://127.0.0.1:8000/orders/DEMO-1003
curl -s http://127.0.0.1:8000/tickets -H 'Content-Type: application/json' -d '{"question":"Como está o pedido?","request_type":"order_status","order_id":"DEMO-1003"}'
curl -s http://127.0.0.1:8000/tickets -H 'Content-Type: application/json' -d '{"question":"Qual a política de cancelamento?","request_type":"order_policy","order_id":"DEMO-1002"}'
```

`GET /orders/{order_id}` retorna 200 para encontrado, 404 para inexistente, 422 para formato inválido e 503 para arquivo indisponível ou inválido. Métodos de alteração retornam 405. O conjunto inteiro é validado antes de qualquer resultado: IDs únicos, timestamps com fuso, totais coerentes, estados conhecidos e ausência de campos extras.

`POST /tickets` aceita três tipos explícitos:

| request_type | Comportamento |
| --- | --- |
| policy (padrão) | Consulta políticas; não aceita order_id. Compatível com o corpo anterior contendo somente question. |
| order_status | Exige order_id; consulta o registro sem chamar modelos. |
| order_policy | Exige order_id; consulta o registro e depois a política. Disponível em demo e grounded; ollama retorna 422. |

O ID vem exclusivamente do campo validado, nunca é extraído ou escolhido pelo modelo. Campos extras são rejeitados. Se o pedido não existir ou a fonte falhar, /tickets retorna HTTP 200 com abstention, skipped_order_lookup e o motivo em order_lookup; não consulta políticas. O resultado de GET usa os códigos HTTP acima.

A resposta combinada separa o estado do pedido da orientação geral, preservada em policy_section. Essa orientação não estabelece elegibilidade para cancelamento ou reembolso. Dados do pedido não são enviados ao modelo. O rastro inclui argumentos, resultado, duração, versão da ferramenta, hash da fonte e mutations_executed=0. O snapshot aparece na mensagem e na fonte; citations continua reservado às políticas.

`order_lookup.synthetic=true` identifica a natureza fictícia dos registros em todos os modos. O campo legado simulated indica apenas mode=demo. needs_review permanece verdadeiro. O roteamento é determinístico, controlado por request_type; não há agente escolhendo ferramentas, confirmação, alteração ou banco de pedidos.

Validação em 17/11/2026: 81 testes unitários e ASGI passaram (57 anteriores e 24 novos). Cobrem os cinco estados, inexistência, corrupção, validação de contratos, isolamento do ID, bloqueio de alterações e serialização HTTP. A composição grounded foi testada com resposta de política simulada; não houve nova avaliação com modelos reais nesta entrega. Os resultados históricos de qualidade do seletor permanecem inalterados.
