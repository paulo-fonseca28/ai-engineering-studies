# SupportOps AI

Assistente de suporte para uma operação **fictícia** de delivery. Consulta seis políticas sintéticas e prepara respostas com fontes; não consulta pedidos reais nem executa cancelamentos, reembolsos ou encaminhamentos.

## O que funciona

- Ingestão de Markdown, fragmentação e IDs com hash SHA-256 do documento.
- Recuperação lexical em memória (baseline próprio, não BM25).
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

## Avaliação

```bash
.venv/bin/python -m evaluation.run --split dev --mode demo --repeats 3 --output evaluation/reports/local-dev-demo.json
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --mode ollama --repeats 3 --output evaluation/reports/local-dev-ollama.json
```

Escolha um novo nome de saída por experimento; relatórios existentes não são sobrescritos. O protocolo contém 21 casos em cada conjunto: 12 respondíveis, 3 ambíguos, 3 sem resposta e 3 adversariais. Veja [método e limites](evaluation/README.md). Métricas de citações verificam documentos/IDs, não correção semântica da resposta.

## Engenharia e próximos passos

Dependências diretas em `requirements.in`; ambiente validado com versões transitivas fixadas em `requirements.txt`. Template de CI em `docs/ci-tests.yml`; ativação no GitHub Actions depende de credencial com permissão de workflows. CI remoto não executado.

Próximas etapas: comparar recuperação semântica e híbrida no desenvolvimento, avaliar ataques em documentos recuperados, revisar respostas, adicionar PostgreSQL/pgvector, pedidos sintéticos, ferramentas com confirmação/idempotência, interface e n8n.

[Arquitetura](docs/architecture.md) · [Limitações](docs/limitations.md) · [Decisões](docs/decisions/0002-evaluation.md)
