# Ponto de retomada — 31/10/2026

## Estado confirmado

O projeto ativo é `projects/supportops-ai`; DemandLab continua planejado, sem implementação. O usuário pediu continuidade entre sessões, READMEs coerentes e preservação dos resultados. A sessão foi encerrada por limite de tokens, não por conclusão do incremento.

Antes deste checkpoint, HEAD: `0714268`. Commits locais anteriores: `763f821` (modo grounded), `827fd73` (resultados da primeira tentativa), `0714268` (contrato de escolha única). O código corrente usa `supportops/prompts/select-v2.txt`. A alteração para referências curtas NÃO foi aplicada: o comando foi interrompido antes de executar. Não presumir que existe select-v3.txt.

55 testes passaram na última alteração de código. Nenhuma mudança de código ocorreu depois disso. Modos demo/ollama e estratégias lexical/semantic/hybrid continuam disponíveis. O padrão é demo + lexical, sem modelos. `grounded` exige semantic e ainda é experimental: a versão atual recusa/esclarece todas as perguntas, sem produzir citações úteis.

## Trabalho desta sessão

- `supportops/grounding.py`: modo restrito com políticas aprovadas por SHA-256, limiar semântico, seleção pelo modelo e renderização determinística de trecho integral ou mensagem fixa. `needs_review` sempre verdadeiro.
- `data/grounding-v3.json`: hashes de seis políticas e digest do embedding; threshold 0.47. Calibrado somente com desenvolvimento v2: preserva 10/12 respondíveis e rejeita 3/3 sem resposta. Não generalizar esse resultado.
- `evaluation/calibrate.py`, métricas adicionais em `evaluation/run.py`, contratos de API e testes adicionados. Configuração incompatível/modelo diferente falha explicitamente.
- Primeira tentativa v3: contrato decision + source_id produziu combinações contraditórias. Desenvolvimento: 27/48 chamadas aceitas, 21 rejeitadas. Relatórios dev-grounded-v3 e heldout-grounded-v3 preservados.
- Correção v3.1: campo único choice com ID longo ou clarify/abstain. Formato passou em 48/48 chamadas de desenvolvimento e 66/66 no conjunto heldout-v4; porém houve ZERO citações em ambos. Isso é falha de utilidade, não sucesso de qualidade. Relatórios com sufixo v3-1 estão preservados neste checkpoint.
- Diagnóstico `evaluation/reports/selector-label-probe-v3.json`: cinco casos de DESENVOLVIMENTO usando referências curtas quote_1 etc., payload reduzido e prompt simplificado. dev-01/02/03 → quote_1; dev-13 ambíguo → quote_2 (falha semântica); dev-19 adversarial → clarify. O relatório contém requests completos, prompt, opções e respostas reais. Não atribuir o efeito só ao comprimento: prompt e payload também mudaram.

## Próximo passo exato

1. Ler este arquivo, `supportops/grounding.py`, os testes de grounding e o relatório selector-label-probe-v3.json. Conferir git status antes de editar.
2. Implementar o payload bem-sucedido do diagnóstico como versão nova, SEM sobrescrever prompts anteriores:
   - Criar `supportops/prompts/select-v3.txt` a partir de `results[0].request.messages[0].content` no relatório do diagnóstico.
   - Alterar PROMPT_PATH para select-v3.txt.
   - Em select_policy, criar `references = {f"quote_{i}": source["id"] for i, source in enumerate(sources, 1)}`.
   - Enviar `candidates` com reference, title e text; não enviar os hashes ao modelo.
   - Schema choice enum = list(references) + ["clarify", "abstain"].
   - Mapear a escolha quote_N de volta ao ID original antes de chamar render; IDs públicos e hashes devem permanecer auditáveis. Escolha desconhecida ou propriedade extra deve continuar rejeitada.
   - Adaptar testes de seleção para provider retornar choice=quote_1; mocks de fontes precisam de title; afirmar que citations contém ID original, nunca o alias.
   - Atualizar versão do protocolo para grounding-v3.2, registrar decisão e executar a suíte.
3. Congelar código em commit. Executar PRIMEIRO só desenvolvimento, três repetições, relatório novo `dev-grounded-v3-2.json`. Não iniciar outra avaliação reservada antes de confirmar que o modo produz respostas úteis.
4. Se o desenvolvimento funcionar, verificar API por HTTP: citação conhecida, pergunta fora do domínio, entrada inválida e provedor indisponível. Testar também, em diretórios temporários, documento novo malicioso e alteração de refund.md; confirmar exclusão antes da recuperação. Testes unitários desses caminhos já existem, mas os probes reais da versão final ainda não foram executados.
5. Avaliação final: heldout-v3 e heldout-v4 JÁ FORAM EXECUTADOS e estão expostos. Usá-los só como regressão. Se houver novo teste reservado, elaborar/congelar antes da execução e não ajustar pelos erros dele. Não chamar conjuntos sintéticos escritos pelo mesmo agente de validação humana independente. Não repetir criação de testes para esconder falhas.
6. Publicar relatório consolidado v3 com tentativas malsucedidas, cobertura perdida, integridade literal e relevância separadas. Atualizar READMEs, arquitetura, limitações e .env.example conforme versão final. Preservar todos os relatórios antigos. Verificar links, git diff --check, commit e push.

## Comandos e ambiente

Na pasta `projects/supportops-ai`:

```bash
.venv/bin/python -m unittest discover -s tests -v
export PATH="$HOME/.local/share/supportops-runtime/bin:$PATH"
ollama serve
# Em outro terminal, após verificar disponibilidade:
OLLAMA_MODEL=qwen3:1.7b .venv/bin/python -m evaluation.run --split dev --strategy semantic --mode grounded --repeats 3 --output evaluation/reports/dev-grounded-v3-2.json
```

Ollama foi reiniciado nesta sessão via processo de ferramenta; sua persistência entre sessões NÃO é garantida. Verificar /api/tags e iniciar se necessário. Runtime isolado em ~/.local/share/supportops-runtime/bin/ollama; modelos já baixados: qwen3:1.7b e qwen3-embedding:0.6b. Hardware observado anteriormente: RTX 3060 12 GB. Sem custos de API externa. Não instalar novamente sem verificar.

Workspace com sandbox somente leitura: comandos de escrita/rede/testes com temporários exigem escalonamento. Não contornar permissões. GitHub CLI já autenticado; SSH falhou anteriormente. Usar remote HTTPS e `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin main`. Token sem permissão workflow: CI fica em docs/ci-tests.yml, não criar .github/workflows sem resolver isso. Não imprimir credenciais.

## Limites que devem continuar explícitos

Citação literal impede paráfrase livre na saída grounded, mas não garante relevância nem política correta. A confiança do manifesto depende de revisão do conteúdo e de controle sobre quem altera código/manifesto. Não equivale a proteção geral contra prompt injection. O modelo ainda escolheu uma política para pergunta ambígua no diagnóstico. Textos do modo ollama continuam sujeitos às falhas documentadas nas versões anteriores. Nenhuma ação externa é executada.

A API segue local, sem autenticação, pedidos reais, banco persistente ou n8n. Próximas entregas maiores, após estabilizar esta fatia: pedidos sintéticos, ferramentas delimitadas, confirmação/idempotência, interface, persistência e integração n8n. Manter docs técnicas e públicas focadas no projeto e no estudo.
