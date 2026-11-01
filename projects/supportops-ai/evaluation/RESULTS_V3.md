# Respostas com políticas aprovadas — v3.2

Avaliação concluída em 01/11/2026. O modo `grounded` voltou a produzir respostas úteis com referências curtas para o modelo e IDs completos na API. As citações exibidas preservam integralmente o fragmento aprovado. Isso controla o texto exibido, mas não garante que o modelo escolha a política certa ou esclareça ambiguidades.

## Implementação avaliada

Código do seletor congelado em `8d5bdea`; perguntas finais e verificador de runtime congelados em `0142321`. Modelo de seleção Qwen3 1.7B, embeddings Qwen3 Embedding 0.6B e Ollama 0.40.13. Digests, opções, versões e hashes constam nos JSONs. O limiar 0,47 e as políticas não mudaram após a calibração em desenvolvimento.

O modelo recebe referências como `quote_1` e devolve uma única escolha: uma referência, `clarify` ou `abstain`. A aplicação mapeia a referência para o ID original e monta a citação integral ou mensagem fixa. Todas as respostas grounded exigem revisão por regra da aplicação. Não há ações externas.

## Resultados da versão final

| Medida | Desenvolvimento (21 perguntas) | Heldout-v5 (24 perguntas) |
| --- | --- | --- |
| Respondíveis com citação do documento esperado | 10/12 (83,3%) | 12/12 (100%) |
| Fontes esperadas recuperadas após o limiar, Recall@3 | 83,3% | 100% |
| Casos sem resposta que não receberam citação | 3/3 | 4/6 |
| Ambiguidades que receberam esclarecimento | 0/3 | 1/3 |
| Chamadas ao seletor com contrato aceito | 48/48 | 63/63 |
| Citações com texto literal preservado | 45/45 | 57/57 |
| Latência mediana do fluxo | 126,329 ms | 149,031 ms |
| Latência p95 do fluxo | 163,486 ms | 251,052 ms |
| Tokens de entrada do seletor | 16.140 | 23.004 |
| Tokens de saída do seletor | 555 | 732 |

Foram 135 execuções do fluxo, três repetições por pergunta, e 111 chamadas reais ao seletor; as demais foram recusadas antes dele. As frações de perguntas são calculadas sobre casos distintos; repetições não são novas perguntas independentes. Latências incluem recuperação e eventuais recusas sem seleção. Tokens de embeddings não foram contabilizados; custo financeiro não foi estimado.

O conjunto heldout-v5 foi escrito e congelado antes da execução final; nenhum ajuste foi feito depois de observar seus resultados. É sintético, elaborado pelo mesmo agente e baseado nas mesmas seis políticas. Não é validação humana independente nem medida de generalização de domínio. Agora que foi inspecionado, deve ser tratado como regressão.

## Falhas que continuam presentes

- `dev-04` e `dev-08`: perguntas respondíveis bloqueadas pelo limiar. A perda de cobertura foi prevista pela calibração.
- `heldout-v5-13`: pergunta por protocolo de revisão de um pedido específico recebeu uma política geral de reembolso, que não contém o protocolo.
- `heldout-v5-15`: pergunta por WhatsApp recebeu política de itens faltando, sem fornecer nem reconhecer a ausência do contato.
- `heldout-v5-19` e `heldout-v5-21`: o modelo escolheu endereço/itens faltando quando deveria esclarecer a intenção.
- Os três ataques pela pergunta no heldout-v5 receberam políticas literais, sem afirmar ação executada nem pedir segredo. Isso não equivale a uma avaliação geral de resistência a prompt injection.

As citações literais removem a redação livre incorreta do caminho grounded, mas permanecem erros de relevância. Integridade literal é uma propriedade verificada do renderizador, não uma nota de acurácia do modelo. O modo `ollama` continua disponível para pesquisa com suas falhas anteriores documentadas.

## Tentativas anteriores preservadas

| Versão | Resultado observado no desenvolvimento |
| --- | --- |
| v3: decision + source_id | 21 das 48 chamadas rejeitadas por combinar recusa/esclarecimento com ID não vazio. |
| v3.1: choice com ID longo | Todas as 48 chamadas passaram pelo formato, mas nenhuma produziu citação útil. |
| v3.2: referências curtas e payload simplificado | 48 chamadas aceitas e citação do documento esperado em 10/12 perguntas respondíveis. |

A mudança não isola o comprimento do ID: prompt e payload também foram simplificados. O [diagnóstico em desenvolvimento](reports/selector-label-probe-v3.json) registra exatamente o que foi testado. Os heldouts v3/v4 executados nas tentativas anteriores não foram reutilizados como teste independente da correção.

## Evidências reproduzíveis

- [Calibração](reports/threshold-v3.json)
- [Desenvolvimento v3](reports/dev-grounded-v3.md) · [Heldout inicial v3](reports/heldout-grounded-v3.md)
- [Desenvolvimento v3.1](reports/dev-grounded-v3-1.md) · [Heldout v4 da v3.1](reports/heldout-grounded-v3-1.md)
- [Desenvolvimento final](reports/dev-grounded-v3-2.md) · [JSON](reports/dev-grounded-v3-2.json)
- [Heldout-v5 final](reports/heldout-grounded-v3-2.md) · [JSON](reports/heldout-grounded-v3-2.json)
- [Verificação operacional](reports/runtime-grounded-v3-2.json)

57 testes automatizados passaram. O verificador real passou em nove solicitações HTTP, quatro verificações de saúde e dois cenários de corpus: arquivo novo com instrução maliciosa e alteração de política existente. Ambos foram excluídos antes da recuperação pelo manifesto. Os checks também confirmaram recusa por limiar, entrada inválida e falhas explícitas de modelo de embeddings/seleção ausente. Isso testa integridade da versão aprovada; não testa a aprovação equivocada de um documento malicioso.

Reexecute os checks com `OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.verify_runtime --output evaluation/reports/local-runtime.json`. O script cria e encerra seus servidores HTTP e usa diretórios temporários; não altera as políticas do projeto.
