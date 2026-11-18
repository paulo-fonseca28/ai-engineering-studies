# Continuidade — 18/11/2026

## Objetivo atual

Usuário pediu concluir todo o SupportOps antes de iniciar DemandLab. Não iniciar DemandLab automaticamente. SupportOps 1.0 concluído como aplicação demonstrável. CI remota aprovada no commit e7b72ee, execução 44373467038, incluindo build Docker. O fechamento documental posterior não altera código. DemandLab aguardará uma nova solicitação.

## Implementação concluída

- API 1.0 e interface completa: pergunta, políticas/fontes, estado simulado, rastros/consumo, histórico e fila local de revisão.
- /tickets aceita order_source=simulation; padrão legado snapshot preservado. Campos simulation_order e order_lookup distinguem fontes. Estado depois de cancelar é refletido na interface.
- SQLite: estado, propostas, execuções, rastros, encaminhamentos e eventos. Cancelamento received → cancelled com proposta de 300s, versão, confirmação e replay atômico. Encaminhamento também confirmado e deduplicado, sem notificar pessoas.
- Token compartilhado configurável; production exige pelo menos 32 caracteres. Não é autenticação por usuário ou autorização por cliente.
- Workflow n8n 2.48.4 importável, executado com webhook autenticado, API e receptor HTTP separado. Falha, recuperação, replay e conflito comprovados, com uma linha por evento em cada banco. Execução demo e grounded reais preservadas em relatórios.
- Dockerfile, Compose, CI em .github/workflows/supportops.yml. Usuário autorizou escopo workflow; gh auth status confirmou repo + workflow.
- Capturas desktop/mobile e vídeo em docs/demo; artigo técnico, guias de execução, operações, integração e licença MIT.

## Validação

103 testes Python, 1 JavaScript, 2 Chromium. Browser executado em demo e grounded, com bancos temporários e token exclusivo de teste. Instalação em venv novo passou e pip check sem conflitos.

Relatórios: evaluation/reports/release-v1-demo.json, release-v1-grounded.json, release-v1-final-grounded.json (17 checks HTTP cada); n8n-v1-runtime.json e n8n-v1-grounded.json (workflow real). Esses checks são de integração, não novo benchmark de qualidade.

Resultados anteriores em evaluation/RESULTS_V3.md são preservados: 12/12 respondíveis finais, mas erros em 2/6 sem resposta e 2/3 ambiguidades. Todos os conjuntos já expostos; não tratar como cegos. Sem revisão humana independente. Não afirmar que relevância foi resolvida.

## Comandos

Na pasta projects/supportops-ai:

```bash
.venv/bin/python -m unittest discover -s tests -q
npm ci
npm run test:ui
npx playwright install --with-deps chromium
npm run test:e2e
.venv/bin/python -m evaluation.verify_release --output evaluation/reports/NOME_NOVO.json
npm ci --prefix integrations/runtime
.venv/bin/python -m evaluation.verify_workflow --n8n integrations/runtime/node_modules/.bin/n8n --grounded --output evaluation/reports/NOME_NOVO.json
```

Grounded exige Ollama e modelos locais qwen3:1.7b / qwen3-embedding:0.6b. Runtime instalado em ~/.local/share/supportops-runtime/bin/ollama; verificar disponibilidade antes de iniciar. Não reinstalar modelos. Nesta máquina Playwright precisou das bibliotecas extraídas em .tooling/browser-libs/root/usr/lib/x86_64-linux-gnu (LD_LIBRARY_PATH); instalação padrão com --with-deps atende a CI Ubuntu. Ferramentas locais ignoradas em .tooling, não parte da aplicação.

## Encerramento

Código, relatórios, vídeo, capturas e workflow publicados no GitHub. GitHub Actions: https://github.com/paulo-fonseca28/ai-engineering-studies/actions/runs/44373467038 . Testes e build Docker passaram. Compose completo não foi iniciado localmente; integração equivalente API → n8n → sink foi executada em processos separados. Não há experimento longo pendente. Ollama foi iniciado para as verificações; disponibilidade futura não é garantida.

## Publicação e limites

Conferir git status/log antes de agir. Sandbox somente leitura exige escalonamento para escrita, testes e rede. Push HTTPS: git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin main. Nunca presumir término de push/CI; verificar resposta.

Hospedagem pública não contratada/configurada; nenhum host ou orçamento foi definido. Não alegar deploy público. SQLite e busca em memória foram decisões explícitas; PostgreSQL/pgvector e múltiplos agentes não são usados. O projeto é demonstração funcional, não operação de clientes reais. Não incluir informações pessoais de candidatura na documentação pública.
