# Workflow n8n e sistema externo de teste

[Importar workflow](n8n-workflow.json). Fluxo: webhook autenticado → `POST /integrations/tickets` → `POST /events` em um processo HTTP separado com banco próprio.

O webhook recebe:

```json
{
  "event_id": "atendimento-demo-0001",
  "ticket": {
    "question": "Qual a política de cancelamento?",
    "request_type": "order_policy",
    "order_id": "DEMO-1001",
    "order_source": "simulation"
  }
}
```

## Execução reproduzível

Node.js 24 e a venv do projeto:

```bash
npm ci --prefix integrations/runtime
.venv/bin/python -m evaluation.verify_workflow --n8n integrations/runtime/node_modules/.bin/n8n --output evaluation/reports/local-n8n.json
# Com Ollama e os modelos do README rodando:
.venv/bin/python -m evaluation.verify_workflow --n8n integrations/runtime/node_modules/.bin/n8n --grounded --output evaluation/reports/local-n8n-grounded.json
```

O verificador cria uma instalação n8n temporária, importa o workflow e uma credencial efêmera, publica o webhook, inicia a API, força falha com destino desligado, inicia o destino e repete o evento. Confere recibos e contagens diretamente nos bancos. Todos os processos temporários são encerrados. Não requer conta n8n Cloud ou sistema real.

Dependências do runtime estão fixadas em `runtime/package-lock.json`. Os scripts nativos de sqlite3 e isolated-vm são autorizados explicitamente em `runtime/package.json` para npm com política de scripts. Outros conectores opcionais não são usados.

## Importação manual / Docker

`docker compose --profile integration up --build` inicia aplicação, n8n e o sink de teste. Abra o n8n em http://127.0.0.1:5678, configure o usuário local, importe o JSON e associe uma credencial **Header Auth** ao webhook, com nome `X-Workflow-Key` e valor escolhido fora do repositório. Publique o workflow.

A instância deve receber as variáveis abaixo antes de iniciar:

- `SUPPORTOPS_API_URL`: URL interna da API, sem barra final.
- `SUPPORTOPS_SINK_URL`: URL interna do receptor de teste, sem barra final.
- `SUPPORTOPS_API_KEY` / `SUPPORTOPS_SINK_KEY`: tokens dos respectivos serviços, quando habilitados.
- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`: permite resolver essas variáveis nos dois nós HTTP. Use apenas workflows confiáveis nessa instância local.

Compose já define os endereços internos. No uso sem Docker, inicie o receptor com `.venv/bin/uvicorn integrations.sink:app --host 127.0.0.1 --port 8001` e configure `SUPPORTOPS_SINK_DB` para um banco separado. O webhook publicado é `/webhook/supportops-demo`; envie `X-Workflow-Key` com a credencial configurada.

## Falhas, repetição e garantias

Os nós HTTP tentam novamente até três vezes. Erros do destino/API fazem a execução falhar; o webhook não confirma registro bem-sucedido quando o destino está fora. As execuções do n8n preservam erros e saídas. Um evento idêntico recupera o mesmo atendimento e o mesmo recibo externo. Reutilizar seu ID com conteúdo diferente é conflito.

A API e o receptor deduplicam em bancos separados; não há transação distribuída. A API pode ter concluído o atendimento antes de falhar a entrega. Reenvie o mesmo evento para recuperar. Repetições simultâneas podem repetir inferência somente leitura, mas só um recibo é persistido. O verificador demonstra falha, recuperação, replay, conflito e apenas uma linha em cada banco.

O workflow não chama `/handoffs` nem confirma cancelamentos: essas ações continuam exigindo revisão explícita na interface. O receptor é um sistema de teste separado, não um SaaS de produção. Nenhum segredo é exportado no JSON.

Referências de implementação: [CLI do n8n](https://docs.n8n.io/hosting/cli-commands/), [Webhook](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/), [HTTP Request e repetição](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/common-issues/).
