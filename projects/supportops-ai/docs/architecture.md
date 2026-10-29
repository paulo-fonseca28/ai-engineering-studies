# Arquitetura

`POST /tickets` → validação → ingestão/versionamento → recuperação lexical → demonstração ou Ollama → validação de IDs citados → resposta com fontes e rastro.

Baseline lexical próprio com frequência de termos, raridade documental e normalização por tamanho; não é BM25. Índice reconstruído em memória por chamada. Fragmentos de até 900 caracteres, identificados por arquivo, hash SHA-256 e posição. Rastros são devolvidos por execução, sem persistência.
