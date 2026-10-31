# 0004 — Seleção restrita e resposta literal

Os experimentos v1/v2 mostraram que IDs válidos e boa recuperação não bastam: o gerador negou cancelamentos sem base e afirmou ações não executadas. Acrescentar `grounded`, mantendo `ollama` como geração livre de pesquisa e `demo` como demonstração extrativa.

No modo grounded, usar apenas busca semântica com o modelo/digest calibrado. Verificar os hashes dos documentos antes da recuperação. Aplicar similaridade mínima de 0,47 aos candidatos. O modelo retorna apenas uma decisão (`quote`, `clarify`, `abstain`) e o ID de uma fonte. Python monta a citação integral do fragmento aprovado ou uma mensagem fixa. Nenhum texto redigido pelo modelo é exibido. `needs_review` é sempre verdadeiro por regra da aplicação.

O limiar vem de uma grade declarada no script de calibração, aplicada ao desenvolvimento v2. Critério: rejeitar todas as perguntas sem resposta daquele conjunto, preservar o máximo de respondíveis e desempatar pelo menor limiar. Resultado: preserva 10/12 respondíveis e rejeita 3/3 sem resposta. Isso não garante a mesma separação em novos dados. Não se aplica o limiar a scores lexicais ou RRF.

O manifesto `data/grounding-v3.json` representa aprovação explícita de seis documentos sintéticos; não é uma assinatura criptográfica nem uma defesa contra quem pode editar código e manifesto. A aprovação não é automática. Ao alterar uma política, revisar o conteúdo, atualizar deliberadamente seu hash e repetir testes/avaliação; não remover a verificação para fazer passar um documento.

Tradeoff: redação menos natural e mais recusas, com eliminação de paráfrases livres na resposta exibida. Seleção incorreta, contexto insuficiente e ambiguidades continuam possíveis. Não é solução geral de prompt injection nem validação semântica completa. Não há ações externas.

Uma partição nova (`heldout-v3`) foi escrita pelo mesmo agente antes da execução, sem repetir perguntas exatas, para avaliação após congelar configuração. Ela não tem anotação humana independente e compartilha as mesmas seis políticas. Após ser inspecionada, vira regressão; não ajustar configuração com seus erros nesta versão.
