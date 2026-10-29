# AI Engineering Studies

Estudos pessoais de engenharia de IA com implementações reproduzíveis e resultados verificáveis. Código, testes, documentação e evidências evoluem juntos por entrega.

## SupportOps AI

Assistente experimental para uma operação fictícia de delivery: API FastAPI, políticas versionadas, busca lexical/semântica/híbrida, geração local com fontes e rastreamento. Modo demonstrativo disponível sem credenciais. Não executa ações externas nem consulta dados reais.

**Estado verificado:** 36 testes automatizados passaram, inferência local executada e novas estratégias verificadas por HTTP. No desenvolvimento, Recall@1 foi de 50% para lexical, 100% para semântica e 91,7% para híbrida, em apenas 12 perguntas respondíveis. A geração ainda apresenta contradições e citações indevidas; respostas exigem revisão.

- [Execução e arquitetura](projects/supportops-ai/README.md)
- [Resultados v2: recuperação e fidelidade](projects/supportops-ai/evaluation/RESULTS_V2.md)
- [Baseline v1 e suas falhas](projects/supportops-ai/evaluation/RESULTS.md)

A revisão de fidelidade é assistida por IA, sem validação humana independente. Não há alegações de uso em produção ou impacto de negócio. Próximo incremento: rejeição de evidências insuficientes e melhoria da geração, seguida de nova avaliação reservada.
