# Fechamento técnico — SupportOps AI 1.0

A entrega implementa o fluxo de estudo completo: pergunta → pedido simulado e políticas → inferência local opcional → resposta com fontes e rastro → revisão local confirmada. Cancelamento sintético é uma ação separada, com proposta e idempotência. Inclui interface, histórico, autenticação por token configurável, workflow n8n, sistema externo de teste, empacotamento e demonstração.

## Evidências executadas

| Verificação | Evidência |
| --- | --- |
| 103 testes Python | Contratos, modelos com mocks, falhas, autenticação, concorrência, rollback, replay e persistência. |
| 1 teste JavaScript | Consentimento e preservação da chave após erro de rede. |
| 2 testes Chromium | Desktop/mobile, fontes, revisão, cancelamento, estado persistido, sem erros de página ou overflow horizontal. Executados em demo e grounded. |
| 17 checks HTTP demo | [Relatório](../evaluation/reports/release-v1-demo.json). |
| 17 checks HTTP grounded | [Relatório](../evaluation/reports/release-v1-grounded.json): política de cancelamento citada integralmente, 240 tokens de entrada e 9 de saída nessa chamada. |
| n8n real + HTTP externo de teste | [Relatório](../evaluation/reports/n8n-v1-runtime.json): autenticação, destino indisponível, recuperação, replay e conflito; uma linha em cada banco. |
| Instalação limpa | Venv novo a partir de requirements.txt, imports e pip check passaram. |
| Demonstração | [Vídeo](demo/supportops-demo.webm), [desktop](demo/supportops-desktop.png), [mobile](demo/supportops-mobile.png). |

Os checks de integração não são uma nova avaliação de qualidade do LLM. Os [resultados v3](../evaluation/RESULTS_V3.md), incluindo erros de relevância/ambiguidade, permanecem válidos e preservados. Não houve validação humana independente.

A versão final do contrato também passou nos [17 checks grounded](../evaluation/reports/release-v1-final-grounded.json). O [workflow com inferência real](../evaluation/reports/n8n-v1-grounded.json) passou por webhook, modelo local e sistema de teste, incluindo recuperação e deduplicação.

## Escopo e encerramento

Concluídos: aplicação local, inferência real, ferramentas delimitadas, confirmação, persistência, fontes/rastros, testes dos caminhos críticos, workflow importável/executável, relatórios por comando, capturas/vídeo e documentação técnica.

CI e build Docker: configuração publicada nesta entrega; o resultado da execução remota será registrado após conclusão. Hospedagem pública não foi contratada/configurada. Isso é uma dependência de ambiente separada, não uma capacidade demonstrada.

Decisões explícitas: SQLite e busca em memória atendem este corpus; não foram introduzidos PostgreSQL/pgvector ou múltiplos agentes apenas para acrescentar tecnologias. Autenticação é compartilhada, não autorização por cliente. A aplicação permanece de demonstração, sem dados ou operações reais.
