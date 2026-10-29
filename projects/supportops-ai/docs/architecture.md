# Arquitetura

`POST /tickets` → validação → ingestão/versionamento → recuperação lexical → demonstração ou Ollama → validação de contrato/IDs citados → resposta com fontes e rastro.

O baseline pontua frequência de termos e raridade documental, normalizando pelo tamanho do fragmento. Não é BM25. Índice reconstruído em memória por chamada. Fragmentos têm até 900 caracteres, com arquivo, SHA-256 e posição. Conteúdo após um título é preservado mesmo sem linha em branco.

`supportops/core.py` contém ingestão, recuperação e fluxo. `supportops/llm.py` isola o provedor e carrega `supportops/prompts/answer-v1.txt`. A saída é limitada por JSON Schema e validada novamente em Python. Não há ferramentas externas; o modelo apenas redige. Validação de formato não comprova fidelidade semântica.

`inference_status` torna explícitos demonstração, ausência de fontes, inferência concluída e erro. Rastros não são persistidos. O runner em `evaluation/run.py` arquiva respostas, métricas, hashes e identificação do provedor. API e avaliação usam o mesmo fluxo.
