# Arquitetura atual

`POST /tickets` valida a pergunta e o tipo explícito de solicitação. service.py encaminha consultas de políticas ao mesmo núcleo utilizado na avaliação e consultas de pedidos à ferramenta somente leitura. O modo padrão demo usa busca lexical; ollama permite geração livre de pesquisa; grounded exige busca semântica e seleção restrita.

## Fluxo grounded

```mermaid
flowchart LR
    A[Pergunta validada] --> B[Documentos com hash aprovado]
    B --> C[Busca semântica]
    C --> D[Limiar de similaridade]
    D --> E[Seleção de referência curta]
    E --> F[Citação literal ou mensagem fixa]
    F --> G[Resposta com fontes e revisão obrigatória]
```

Falta de fontes, exclusão por limiar e falhas de provedor/configuração devolvem recusa com estado explícito. O modelo escolhe entre referências temporárias como quote_1, clarify e abstain. Python converte a referência no ID original e renderiza o texto completo aprovado. O modelo não pode fornecer o texto exibido neste modo.

## Componentes

- `core.py`: ingestão, baseline lexical, orquestração e rastreamento.
- `retrieval.py`: busca semântica e híbrida RRF, validação e cache em memória de vetores de documentos.
- `llm.py`: geração livre com `answer-v1.txt`; falhas semânticas conhecidas permanecem documentadas.
- `grounding.py`: manifesto, limiar, seletor com `select-v3.txt`, mapeamento de referências e renderização literal.
- `data/grounding-v3.json`: versões aprovadas das políticas e modelo de embeddings calibrado.
- `evaluation/run.py`: execução e métricas; `calibrate.py`: seleção do limiar somente no desenvolvimento; `verify_runtime.py`: checks reais por HTTP e integridade de corpus.

Fragmentos de até 900 caracteres referenciam arquivo, SHA-256 e posição. A recuperação é recalculada em memória; o cache de documentos usa conteúdo, digest e endpoint. Não há PostgreSQL/pgvector nesta etapa. Rastros de API são devolvidos na resposta, sem persistência; os experimentos arquivam rastros em JSON.

Há consulta de pedidos sintéticos via orders.py, com validação integral do arquivo, hash e snapshot. service.py combina o registro com uma seção independente de política, sem enviar dados do pedido ao modelo. O roteamento usa request_type, não uma decisão do LLM. O fluxo de tickets não executa alterações. A API /simulation oferece cancelamento sintético em SQLite via actions.py, com proposta e confirmação explícitas em endpoints separados. Veja [contrato e fluxo](order-tool.md). Revisão obrigatória é um campo de saída, não encaminhamento executado. Citação literal não prova que a política escolhida responda à pergunta.

## Estado da simulação

`actions.py` mantém orders, proposals e executions em uma única transação SQLite por operação. Versão do pedido evita confirmar uma proposta desatualizada; chave de idempotência recupera o resultado original. As consultas de tickets continuam no snapshot estático. [Contrato, exemplos e limites](simulation.md).

## Interface local

GET / entrega ui.html e GET /ui.js entrega o script sem dependências externas. O navegador consulta exclusivamente /simulation, exige consentimento e mantém a mesma chave ao repetir uma confirmação após erro de rede. Dados retornados são inseridos via textContent. Não há chamadas de modelo na tela.
