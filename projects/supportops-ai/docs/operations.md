# Operação local e empacotamento

## Configuração

A aplicação Python lê variáveis exportadas; Docker Compose pode ler `.env`. Não versionar segredos. Modo padrão demo/lexical dispensa modelos; grounded exige semantic e os modelos aprovados no manifesto. `/health` verifica o processo, não o modelo ou a durabilidade do armazenamento.

Use `SUPPORTOPS_API_KEY` para exigir Bearer token nos dados e operações. A interface recebe a chave em campo de senha e a guarda apenas em memória. `SUPPORTOPS_ENV=production` recusa iniciar sem chave de ao menos 32 caracteres. HTML, CSS, JavaScript, health e esquema OpenAPI são públicos; não contêm registros. Em hospedagem remota, TLS e configuração correta do proxy são responsabilidades do ambiente. Não habilitamos CORS entre origens.

O token é compartilhado: não há contas, propriedade de pedido ou papéis. Esta é uma aplicação de estudo com dados sintéticos, não uma configuração pronta para atendimento de clientes reais.

## Dados e backup

`SUPPORTOPS_ACTION_DB` aponta para o SQLite de pedidos, propostas, execuções, atendimentos, encaminhamentos e recibos. O padrão é `var/actions.sqlite3`; diretórios são criados no primeiro acesso. Inicialização usa a fixture validada uma única vez. Reinícios não repopulam nem desfazem cancelamentos.

Esquema 0 da versão anterior migra aditivamente para v1; uma versão futura desconhecida é recusada. Não existe downgrade automático. Para outra demonstração, use um caminho novo, em vez de apagar o banco existente.

Antes de atualizar, pare a aplicação e copie o arquivo do banco para um destino novo. Se preferir backup online, use a API `sqlite3.Connection.backup` do Python. Preserve permissões e teste a restauração numa cópia apontada por `SUPPORTOPS_ACTION_DB`; não substitua o banco ativo. O sink e o n8n têm bancos/volumes separados e precisam de backups próprios. Retenção/limpeza não são automáticas.

## Docker

```bash
docker compose up --build
# Incluindo os serviços opcionais:
docker compose --profile integration up --build
```

A aplicação roda como usuário sem privilégios, com volume em `/app/var` e health check. As portas publicadas ficam em localhost. `docker compose down` preserva os volumes; não use `down -v` se precisar manter os registros.

Grounded usa Ollama no host por `host.docker.internal`. O Ollama precisa aceitar a conexão a partir da rede do Docker; o binding padrão exclusivo em 127.0.0.1 pode impedir isso. Ajuste o endereço de escuta e as regras locais deliberadamente; não exponha Ollama publicamente. A execução Python direta evita essa configuração de rede.

## CI e hospedagem

O workflow `.github/workflows/supportops.yml` executa testes Python, JavaScript, navegador, verificação HTTP sem modelos e build Docker. Os relatórios e artefatos ficam anexados à execução. Testes com modelos locais e n8n têm comandos reproduzíveis próprios; não dependem de credenciais no CI padrão.

A publicação do código no GitHub não equivale à hospedagem da API. Não foi contratado ou configurado servidor público, domínio ou conta paga. A entrega inclui execução local, imagem/Compose e roteiro. Um deploy público exigirá escolher destino, persistência, HTTPS, segredos e recursos para os modelos; não alegamos que essa operação já existe.
