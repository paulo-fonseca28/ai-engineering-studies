# SupportOps AI

> **Checkpoint de 31/10/2026:** o modo `grounded` está em desenvolvimento. A versão atual passou em 55 testes, mas recusou/esclareceu todas as perguntas nos últimos experimentos; a correção com referências curtas ainda está pendente. O padrão demo + lexical continua disponível. Veja o [ponto de retomada](../../CONTINUITY.md).

Assistente de suporte para uma operação **fictícia** de delivery. Consulta seis políticas sintéticas e prepara respostas com fontes; não consulta pedidos reais nem executa cancelamentos, reembolsos ou encaminhamentos.

## O que funciona

- Ingestão de Markdown, fragmentação e IDs com hash SHA-256 do documento.
- Recuperação lexical, semântica com embeddings locais e híbrida por fusão de rankings.
- API FastAPI com contratos de entrada e saída, rastro e duração por solicitação.
- Modo demonstrativo sem credenciais e integração local com Ollama, prompt versionado e saída estruturada.
- Avaliação por comando, com conjuntos separados de desenvolvimento/teste e relatórios JSON/Markdown.
- Testes de API, recuperação, falhas do provedor, citações e cálculo das métricas.

## Executar (Python 3.12)

```bash
cd projects/supportops-ai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/docs para enviar perguntas e inspecionar o contrato.

```bash
curl -s http://127.0.0.1:8000/tickets -H 'Content-Type: application/json' -d '{"question":"Qual a política de reembolso?"}'
.venv/bin/python -m unittest discover -s tests -v
```

O modo `demo` devolve trechos literais e sempre sinaliza revisão humana. Não usa LLM e não mede qualidade de modelo. `needs_review` não abre um chamado externo.

## Inferência real local

Instale [Ollama](https://docs.ollama.com/linux) e inicie `ollama serve` em outro terminal. Depois:

```bash
ollama pull qwen3:1.7b
SUPPORTOPS_MODE=ollama OLLAMA_MODEL=qwen3:1.7b .venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

Se estiver usando a instalação isolada preparada neste ambiente, adicione antes `export PATH="$HOME/.local/share/supportops-runtime/bin:$PATH"`. Ela não instala um serviço de inicialização automática.

O [Qwen3 1.7B](https://ollama.com/library/qwen3:1.7b) é o modelo inicial de experimento, não uma seleção final de qualidade. O adaptador usa `think=false`, temperatura 0, seed 42 e limite de 512 tokens de saída. Estas opções não garantem determinismo entre ambientes.

Endpoint padrão: `http://localhost:11434/api/chat`, configurável por `OLLAMA_URL`. O aplicativo lê variáveis do ambiente; `.env.example` não é carregado automaticamente. Inferência tem timeout de 120 segundos. O campo `inference_status` distingue `completed`, `failed`, `skipped_no_sources` e `demo`; falhas sinalizam revisão e preservam contagens de tokens quando disponíveis. `/health` verifica a aplicação, não a disponibilidade do modelo.

## Estratégias de recuperação

O padrão continua `lexical`, sem dependência de embeddings. Para experimentar a busca semântica:

```bash
ollama pull qwen3-embedding:0.6b
SUPPORTOPS_RETRIEVAL=semantic SUPPORTOPS_MODE=ollama OLLAMA_MODEL=qwen3:1.7b .venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

Use `SUPPORTOPS_RETRIEVAL=hybrid` para fusão RRF. `OLLAMA_EMBEDDING_MODEL` pode alterar o modelo de embeddings; o padrão é `qwen3-embedding:0.6b`. `demo` com busca semântica não gera texto com LLM, mas precisa do serviço de embeddings. Falha de recuperação produz `skipped_retrieval_error` e revisão, sem fallback lexical silencioso.

A busca semântica usa similaridade de cosseno, instrução de consulta e vetores dos documentos em cache por conteúdo, digest do modelo e endpoint. O cache é local ao processo, não um banco persistente. Não há limiar de rejeição: top-k retorna documentos mesmo quando não sustentam uma resposta.

## Respostas restritas com fontes aprovadas

```bash
SUPPORTOPS_MODE=grounded SUPPORTOPS_RETRIEVAL=semantic OLLAMA_MODEL=qwen3:1.7b .venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

Este modo requer os dois modelos já apresentados. O modelo seleciona uma política, pede esclarecimento ou recusa. O código exibe o fragmento integral aprovado ou uma mensagem fixa: não exibe paráfrases geradas. `answer_kind` diferencia `policy_quote`, `clarification` e `abstention`; `needs_review` é sempre verdadeiro.

Documentos precisam corresponder ao manifesto versionado em `data/grounding-v3.json`. Fontes novas/adulteradas são removidas antes da busca. A similaridade mínima de 0,47 foi calibrada apenas em desenvolvimento e vale para o digest indicado no manifesto. Um modelo diferente exige nova calibração. Recusas por limiar aparecem como `skipped_evidence_gate`; falhas de integridade/configuração são explícitas no rastro.

Preservar o texto da política não prova que ela responde à pergunta. O modo troca redação livre por citações e pode recusar perguntas legítimas. Veja [a decisão e os limites](docs/decisions/0004-grounded-responses.md).

## Avaliação

```bash
.venv/bin/python -m evaluation.run --split dev --mode demo --repeats 3 --output evaluation/reports/local-dev-demo.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --mode ollama --repeats 3 --output evaluation/reports/local-dev-ollama.json
```

Escolha um novo nome de saída por experimento; relatórios existentes não são sobrescritos. O protocolo contém 21 casos em cada conjunto: 12 respondíveis, 3 ambíguos, 3 sem resposta e 3 adversariais. Veja [método e limites](evaluation/README.md). Métricas de citações verificam documentos/IDs, não correção semântica da resposta.

## Comparação de recuperação no desenvolvimento

```bash
.venv/bin/python -m evaluation.compare --repeats 3 --output evaluation/reports/local-retrieval.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --strategy semantic --mode ollama --repeats 3 --output evaluation/reports/local-semantic.json
```

[Comparação v2](evaluation/reports/dev-retrieval-v2.md): Recall@1 lexical 50,0%, semântico 100% e híbrido 91,7%, em apenas 12 perguntas respondíveis de desenvolvimento. Ambas as alternativas densas tiveram Recall@3 de 100%, mas retornaram documentos também nos três casos sem resposta. Não é resultado de teste independente nem evidência de correção das respostas.

## Estado atual — v2

**36 testes passaram**, além de verificações HTTP de busca semântica real, híbrida demonstrativa e falha por modelo ausente. Foram executadas 189 buscas comparativas e 63 chamadas reais de geração nesta etapa. A revisão assistida por IA cobriu 42 respostas (21 por estratégia), com justificativas e fontes; não substitui validação humana.

A busca semântica recuperou melhor as paráfrases, mas o gerador ainda contradisse políticas e respondeu fora do domínio com citação indevida. Veja [resultados v2 e decisão técnica](evaluation/RESULTS_V2.md). Não há nova validação independente em teste nem uso autônomo aprovado.

## Resultados do baseline v1

Inferência real validada localmente com Qwen3 via Ollama. **22 testes passaram**, mais verificações por HTTP nos modos demo e real. O experimento congelado realizou 252 execuções de fluxo, incluindo 96 chamadas reais ao modelo.

| Recuperação lexical | Desenvolvimento | Teste |
| --- | --- | --- |
| Recall@3 em perguntas respondíveis | 50,0% (6/12) | 66,7% (8/12) |

O modelo apresentou contradições e afirmações indevidas em casos adversariais, mesmo com citações válidas e revisão sinalizada. O modo real é experimental e exige revisão das respostas. Veja [resultados, exemplos de falhas e latências](evaluation/RESULTS.md); métricas de formato não são acurácia semântica.

## Engenharia e próximos passos

Dependências diretas em `requirements.in`; ambiente validado com versões transitivas fixadas em `requirements.txt`. Template de CI em `docs/ci-tests.yml`; ativação no GitHub Actions depende de credencial com permissão de workflows. CI remoto não executado.

Próximas etapas: avaliar fidelidade e rejeição de evidências insuficientes, validar em novo teste reservado, avaliar ataques em documentos recuperados, adicionar PostgreSQL/pgvector, pedidos sintéticos, ferramentas com confirmação/idempotência, interface e n8n.

[Arquitetura](docs/architecture.md) · [Limitações](docs/limitations.md) · [Decisões](docs/decisions/0002-evaluation.md)
