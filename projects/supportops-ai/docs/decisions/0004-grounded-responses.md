# 0004 — Seleção restrita e resposta literal

Os experimentos v1/v2 mostraram que IDs válidos e boa recuperação não bastam: o gerador negou cancelamentos sem base e afirmou ações não executadas. Acrescentar `grounded`, mantendo `ollama` como geração livre de pesquisa e `demo` como demonstração extrativa.

No modo grounded, usar apenas busca semântica com o modelo/digest calibrado. Verificar os hashes dos documentos antes da recuperação. Aplicar similaridade mínima de 0,47 aos candidatos. O modelo retorna apenas uma decisão (`quote`, `clarify`, `abstain`) e o ID de uma fonte. Python monta a citação integral do fragmento aprovado ou uma mensagem fixa. Nenhum texto redigido pelo modelo é exibido. `needs_review` é sempre verdadeiro por regra da aplicação.

O limiar vem de uma grade declarada no script de calibração, aplicada ao desenvolvimento v2. Critério: rejeitar todas as perguntas sem resposta daquele conjunto, preservar o máximo de respondíveis e desempatar pelo menor limiar. Resultado: preserva 10/12 respondíveis e rejeita 3/3 sem resposta. Isso não garante a mesma separação em novos dados. Não se aplica o limiar a scores lexicais ou RRF.

O manifesto `data/grounding-v3.json` representa aprovação explícita de seis documentos sintéticos; não é uma assinatura criptográfica nem uma defesa contra quem pode editar código e manifesto. A aprovação não é automática. Ao alterar uma política, revisar o conteúdo, atualizar deliberadamente seu hash e repetir testes/avaliação; não remover a verificação para fazer passar um documento.

Tradeoff: redação menos natural e mais recusas, com eliminação de paráfrases livres na resposta exibida. Seleção incorreta, contexto insuficiente e ambiguidades continuam possíveis. Não é solução geral de prompt injection nem validação semântica completa. Não há ações externas.

Uma partição nova (`heldout-v3`) foi escrita pelo mesmo agente antes da execução, sem repetir perguntas exatas, para avaliação após congelar configuração. Ela não tem anotação humana independente e compartilha as mesmas seis políticas. Após ser inspecionada, vira regressão; não ajustar configuração com seus erros nesta versão.

## Correção do contrato — v3.1

No desenvolvimento v3, 21/48 chamadas foram rejeitadas porque o modelo combinou decisão de recusa/esclarecimento com um ID não vazio. A aplicação recusou a saída, mas isso prejudicou a disponibilidade. A causa foi diagnosticada no desenvolvimento; os resultados iniciais estão preservados.

Substituir o contrato de rede por um único campo `choice`, cujo enum contém IDs permitidos, `clarify` e `abstain`. O renderizador converte a escolha em decisão interna. Não há dois campos que possam divergir. Limiar, corpus e opções do modelo permanecem iguais. O prompt `select-v1.txt` fica preservado e `select-v2.txt` descreve a nova representação.

Como heldout-v3 já executou, passa a ser regressão. Criar heldout-v4 antes de executar a correção; mesmas proporções e limitações de autoria/domínio. Não selecionar nova configuração usando seus resultados.

## Referências curtas — v3.2

A v3.1 passou pelo contrato mas não produziu citações úteis no desenvolvimento. O diagnóstico em cinco casos de desenvolvimento com referências curtas produziu citações nas três perguntas respondíveis, mas escolheu política numa pergunta ambígua. Adotar o payload e o prompt exatos desse diagnóstico como candidato v3.2, sem atribuir a diferença apenas ao comprimento dos IDs: prompt e payload também mudaram.

O modelo recebe reference, title e text. A aplicação converte quote_N no ID original, valida que a referência existe e continua renderizando o texto integral aprovado. IDs/hash públicos não mudam. O prompt select-v3.txt é versionado; os anteriores permanecem preservados. Limiar, corpus e opções do modelo não mudam.

## Congelamento para validação v3.2

O desenvolvimento v3.2 produziu citações do documento esperado em 10/12 perguntas respondíveis, sem erro de contrato; ambiguidades ainda receberam políticas. Não ajustar o limiar nem o seletor nesta etapa. Criar heldout-v5 com 24 perguntas antes da execução final (12 respondíveis, 6 sem resposta, 3 ambíguas e 3 adversariais). Todas as partições anteriores estão expostas. A nova partição continua sintética e de autoria do agente, não validação humana independente. Seus erros devem ser publicados, não usados para outra rodada de ajuste nesta entrega.
