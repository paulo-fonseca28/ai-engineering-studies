# Ponto de retomada — 17/11/2026

## Entrega atual — cancelamento sintético com confirmação

API 0.6: actions.py implementa SQLite em var/actions.sqlite3 (ou SUPPORTOPS_ACTION_DB), inicializado da fixture uma vez. /simulation/orders/{id} lê estado; /simulation/cancellations/proposals prepara cancelamento received → cancelled; /simulation/cancellations/confirmations exige confirmed=true, proposal_id e idempotency_key. Proposta expira em 300s; versão evita confirmação obsoleta; BEGIN IMMEDIATE torna mudança, consumo e resultado atômicos. Repetições recuperam o resultado original. Não há modelo executando ferramentas.

91 testes passaram em 17/11/2026. Dez novos cobrem concorrência, persistência, rollback, contratos ASGI e erros. Sem nova avaliação de LLM. Documentação em docs/simulation.md. Bancos ignorados pelo Git; testes usam temporários. /orders e /tickets continuam no snapshot estático, explicitamente separado de /simulation. Não inferir que o cancelamento altera o snapshot.

Próxima etapa: interface local de revisão/confirmacão e decisão explícita sobre integrar consultas ao estado simulado; autenticação e migrações seguem pendentes. Evitar misturar fonte estática e mutável silenciosamente. DemandLab ainda planejado. Revisar status/log ao retomar; relatórios e limitações do seletor preservados.

## Entrega anterior de pedidos — 17/11/2026

API 0.5: lookup_order somente leitura, fixture com cinco estados, contratos estritos e rastros. GET /orders/{id}; POST /tickets aceita policy (padrão), order_status e order_policy. O último aceita demo/grounded, bloqueia geração livre ollama. ID explícito obrigatório, nenhum ID inferido pelo modelo. Registro ausente/corrompido impede consulta de políticas. Nenhuma alteração implementada.

81 testes passaram: 57 anteriores e 24 novos, incluindo integração ASGI. Contratos em docs/lookup-order.schema.json e exemplos/limites em docs/order-tool.md. Composição grounded validada com mocks, sem novos resultados reais de LLM. Relatórios anteriores preservados. Não há execução longa pendente nesta entrega.

Plano anterior, concluído na simulação acima: desenhar e implementar alteração estritamente sintética com confirmação explícita e idempotência, definindo persistência e transições antes de expor ações. Não apresentar consulta atual como agente autônomo. As falhas anteriores de relevância continuam abertas. DemandLab ainda não implementado. Conferir git status/log; não reutilizar avaliações expostas como teste cego.

## Estado anterior e evidências preservadas

SupportOps AI: modo grounded v3.2 implementado, avaliado e documentado. DemandLab continua planejado, sem implementação. O usuário solicita progresso contínuo, READMEs coerentes e preservação do contexto entre sessões. Não considerar os dois projetos concluídos.

Commits desta entrega antes da consolidação documental:
- `8d5bdea`: referências curtas no seletor e testes; avaliação de desenvolvimento.
- `0142321`: congelamento do heldout-v5, resultados de desenvolvimento e checks operacionais reproduzíveis.

A documentação/relatórios/checkpoint foram consolidados em commit posterior. Conferir git status e log ao retomar. O checkpoint antigo de 31/10 foi substituído; seu histórico continua no Git.

## O que foi concluído

- Aplicado o payload do diagnóstico preservado em selector-label-probe-v3.json. Prompt ativo: `supportops/prompts/select-v3.txt`; anteriores preservados.
- O modelo vê reference/title/text, escolhe quote_N/clarify/abstain e a aplicação converte quote_N no ID original. Nenhum texto livre do modelo é exibido em grounded.
- Limiar e corpus não mudaram: `data/grounding-v3.json`, threshold 0.47, hashes aprovados e digest do embedding.
- 57 testes passaram. Regressões cobrem referências de segunda fonte, manutenção do ID original e rejeição de referências desconhecidas/propriedades extras.
- Desenvolvimento: 10/12 respondíveis com citação esperada, duas recusadas pelo limiar; 48/48 chamadas com contrato aceito. Ambiguidades ainda recebem políticas em vez de esclarecimento.
- Heldout-v5, congelado antes da execução: 12/12 respondíveis com política esperada; 4/6 sem resposta sem citação; 1/3 ambiguidades esclarecidas. 63/63 chamadas aceitas. Todas as citações preservaram integralmente o texto.
- 9 solicitações HTTP, 4 health checks e 2 probes reais de integridade de corpus passaram. Dependências passaram no pip check.
- Relatório consolidado `projects/supportops-ai/evaluation/RESULTS_V3.md`; todos os resultados iniciais malsucedidos preservados.

## Falhas ainda relevantes

`heldout-v5-13` pediu protocolo de um pedido e recebeu política geral; `heldout-v5-15` pediu WhatsApp e recebeu política de itens. `heldout-v5-19/21` eram ambíguos e receberam políticas. Não confundir texto literal com resposta adequada. Nenhuma ação foi executada. `needs_review` sempre verdadeiro em grounded é uma regra, não competência do modelo.

Todos os conjuntos existentes (dev, test, heldout-v3/v4/v5) já foram usados/expostos. Não reutilizar como validação independente nem ajustar configuração pelos erros finais sem declarar regressão. Se criar uma nova avaliação reservada, congelar antes e não repetir criação de testes para esconder erros. Dados/avaliações são sintéticos, sem validação humana independente. O modo ollama mantém geração livre de pesquisa com falhas documentadas.

## Plano anterior (consulta já concluída acima)

Avançar o produto com consulta somente leitura de pedidos sintéticos e contratos de ferramentas explícitos, antes de qualquer ação de alteração. Preservar revisão humana e limitar a resposta aos campos fornecidos pela ferramenta e políticas aprovadas. Cobrir ID inexistente, estados do pedido e rastreamento; não inventar ações executadas. Confirmação/idempotência, persistência, interface e n8n seguem como etapas posteriores. A melhoria de ambiguidades/evidência insuficiente permanece uma pendência explícita; não anunciar resolução.

Se a prioridade for nova melhoria do seletor, usar apenas desenvolvimento para ajustes e comparar cobertura/recusa. Não repetir a calibração atual sem motivo nem sobrescrever relatórios. O modo padrão demo + lexical continua offline; grounded exige semantic.

## Executar

Na pasta `projects/supportops-ai`:

```bash
.venv/bin/python -m unittest discover -s tests -v
export PATH="$HOME/.local/share/supportops-runtime/bin:$PATH"
ollama serve
# Em outro terminal:
SUPPORTOPS_MODE=grounded SUPPORTOPS_RETRIEVAL=semantic OLLAMA_MODEL=qwen3:1.7b .venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.verify_runtime --output evaluation/reports/local-runtime.json
```

Use um nome de saída ainda inexistente. Ollama 0.40.13 foi iniciado nesta sessão por ferramenta; sua persistência não é garantida. Verificar /api/tags antes de reiniciar. Modelos qwen3:1.7b e qwen3-embedding:0.6b já estão baixados. Runtime em ~/.local/share/supportops-runtime/bin/ollama. Não reinstalar sem verificar. Os servidores HTTP temporários do verificador foram encerrados; não há avaliação longa pendente.

## Repositório e permissões

Sandbox somente leitura: escrita, rede e testes com temporários exigem escalonamento. GitHub autenticado, remote HTTPS. Para push: `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin main`. Não imprimir credenciais. A credencial não tem permissão workflow; CI segue como template em docs/ci-tests.yml, não ativo. Não presumir que um push terminou: verificar a resposta e estado Git.

Manter documentação pública focada nos estudos/implementação, sem informações pessoais de candidatura. Atualizar README, arquitetura, limitações e este checkpoint ao terminar a próxima entrega. O projeto ainda não tem autenticação, dados reais, ferramentas de alteração de pedidos reais, n8n, interface própria ou deploy público da aplicação.
