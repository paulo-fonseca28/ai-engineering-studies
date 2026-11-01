# SupportOps AI

Assistente experimental para uma operação **fictícia** de delivery. Consulta seis políticas sintéticas e devolve orientações com fontes e rastreamento. Não consulta pedidos reais nem executa cancelamentos, reembolsos ou encaminhamentos.

## Estado verificado

**57 testes passaram**, além de nove solicitações HTTP, quatro checks de saúde e dois testes reais de exclusão de documentos não aprovados. O modo grounded voltou a produzir citações úteis: documento esperado em 10/12 perguntas respondíveis de desenvolvimento e 12/12 da bateria final de 24 perguntas.

Todas as citações grounded preservaram o texto aprovado. Ainda ocorreram políticas irrelevantes em 2/6 perguntas sem resposta e falta de esclarecimento em 2/3 ambiguidades da bateria final. Os dados são sintéticos e não têm validação humana independente. Veja [resultados completos, tentativas anteriores e limites](evaluation/RESULTS_V3.md).

## Executar sem modelos (Python 3.12)

Na raiz do repositório:

```bash
cd projects/supportops-ai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/docs para enviar perguntas. O padrão é demonstração com busca lexical, sem credenciais ou serviço de modelos.

```bash
curl -s http://127.0.0.1:8000/tickets -H 'Content-Type: application/json' -d '{"question":"Qual a política de reembolso?"}'
.venv/bin/python -m unittest discover -s tests -v
```

## Executar com seleção de políticas local

Com [Ollama](https://docs.ollama.com/linux) instalado, inicie `ollama serve` em outro terminal. Na instalação isolada deste ambiente, o executável fica em `~/.local/share/supportops-runtime/bin/ollama`; use `export PATH="$HOME/.local/share/supportops-runtime/bin:$PATH"` para encontrá-lo. Não há serviço de inicialização automática.

```bash
ollama pull qwen3:1.7b
ollama pull qwen3-embedding:0.6b
SUPPORTOPS_MODE=grounded SUPPORTOPS_RETRIEVAL=semantic OLLAMA_MODEL=qwen3:1.7b .venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

O modelo escolhe uma política, esclarecimento ou recusa. Python monta a citação integral aprovada ou uma mensagem fixa; não mostra redação livre do modelo. `answer_kind` distingue `policy_quote`, `clarification` e `abstention`. `needs_review=true` é obrigatório neste modo e não significa que um chamado externo foi aberto.

## Modos e configuração

| Modo | Comportamento | Dependências |
| --- | --- | --- |
| `demo` (padrão) | Exibe trechos recuperados; não gera texto com LLM. | Nenhum modelo com busca lexical; embeddings para semantic/hybrid. |
| `ollama` | Geração livre experimental, com validação de formato/citações. | Modelo de chat e, conforme estratégia, embeddings. |
| `grounded` | Seleção restrita e renderização literal de política aprovada. | Chat, embeddings e estratégia semantic. |

`SUPPORTOPS_RETRIEVAL` aceita `lexical`, `semantic` ou `hybrid`. A busca híbrida usa RRF. O núcleo usa índice em memória; vetores de documentos são reutilizados por conteúdo, digest do modelo e endpoint. Não há banco vetorial persistente.

Variáveis de referência em [.env.example](.env.example); o aplicativo não carrega `.env` automaticamente. `OLLAMA_URL` aponta por padrão para `http://localhost:11434/api/chat`; `OLLAMA_EMBEDDING_MODEL` é `qwen3-embedding:0.6b`. `/health` verifica a aplicação, não a disponibilidade dos modelos. Erros são explícitos em `inference_status` e `trace`, sem fallback silencioso para outra estratégia.

Em grounded, hashes dos documentos são verificados antes da recuperação; fontes novas ou modificadas são excluídas. O limiar de 0,47 e o digest de embeddings vêm de [grounding-v3.json](data/grounding-v3.json). Outro modelo exige recalibração. Ao editar uma política, revisar seu conteúdo, aprovar deliberadamente o novo hash e repetir a avaliação. O manifesto não deve ser atualizado automaticamente durante a execução. Preservação do texto e similaridade não garantem relevância.

## Avaliação e verificação

Execute na pasta do projeto, escolhendo saídas ainda inexistentes:

```bash
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --strategy semantic --mode grounded --repeats 3 --output evaluation/reports/local-dev.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.verify_runtime --output evaluation/reports/local-runtime.json
.venv/bin/python -m evaluation.compare --repeats 3 --output evaluation/reports/local-retrieval.json
```

Relatórios incluem respostas, métricas, hashes e identificação do modelo. As partições já publicadas foram executadas e agora são regressão; não tratá-las como testes cegos para novos ajustes. [Protocolo](evaluation/README.md) · [Resultados v3](evaluation/RESULTS_V3.md) · [Resultados v2](evaluation/RESULTS_V2.md) · [Baseline v1](evaluation/RESULTS.md).

Dependências diretas em `requirements.in` e versões transitivas fixadas em `requirements.txt`. O template [CI](docs/ci-tests.yml) ainda não está ativado: a credencial GitHub atual não permite publicar workflows. CI remoto, Docker e deploy público da aplicação continuam pendentes.

## Próximas entregas

Aprimorar esclarecimento de ambiguidades e tratamento de perguntas sem evidência, mantendo resultados anteriores. Depois, adicionar pedidos sintéticos, ferramentas delimitadas com confirmação/idempotência, persistência, interface e integração n8n. DemandLab permanece um projeto futuro separado.

[Arquitetura](docs/architecture.md) · [Limitações](docs/limitations.md) · [Decisão do modo grounded](docs/decisions/0004-grounded-responses.md) · [Checkpoint](../../CONTINUITY.md)
