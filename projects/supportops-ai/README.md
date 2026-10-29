# SupportOps AI

Suporte para uma operação **fictícia** de delivery. Primeira etapa: ingestão de Markdown com hashes de versão, fragmentação, busca lexical, API validada, fontes e rastreamento.

## Executar (Python 3.12)

```bash
cd projects/supportops-ai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

Documentação interativa: http://127.0.0.1:8000/docs.

```bash
curl -s http://127.0.0.1:8000/tickets -H 'Content-Type: application/json' -d '{"question":"Qual a política de reembolso?"}'
python3 -m unittest discover -s tests -v
```

O modo `demo` retorna trechos literais, não usa LLM e sempre pede revisão humana. Não representa uma avaliação de qualidade de modelo.

## Inferência local opcional

Com Ollama e um modelo já instalado, configure:

```bash
export SUPPORTOPS_MODE=ollama
export OLLAMA_MODEL='nome-do-modelo-instalado'
.venv/bin/uvicorn supportops.api:app --host 127.0.0.1 --port 8000
```

Endpoint padrão: `http://localhost:11434/api/chat`, configurável por `OLLAMA_URL`. O aplicativo lê variáveis do ambiente; `.env.example` é apenas referência. Falhas do provedor ou contratos inválidos encaminham para revisão. A integração possui testes com respostas simuladas; inferência real ainda não foi validada neste ambiente.

## Próximos incrementos

Conjuntos separados de desenvolvimento/teste; comparação lexical/semântica; PostgreSQL/pgvector; consulta de pedidos sintéticos; ferramentas com confirmação e idempotência; interface e n8n.

Veja [arquitetura](docs/architecture.md) e [limitações](docs/limitations.md). Não há ações externas neste incremento.

## Integração contínua

Template em `docs/ci-tests.yml`. Para ativar, mova para `.github/workflows/tests.yml` na raiz usando uma credencial com permissão de workflows. CI remoto ainda não foi executado.
