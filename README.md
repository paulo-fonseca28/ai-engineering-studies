# AI Engineering Studies

Estudos pessoais de engenharia de IA com código, testes, documentação e resultados reproduzíveis.

## SupportOps AI

Assistente experimental para uma operação fictícia de delivery. Implementa API FastAPI, políticas versionadas, busca lexical/semântica/híbrida, inferência local e rastreamento. O modo grounded seleciona políticas aprovadas e devolve citações literais; o modo demonstrativo padrão funciona sem modelos.

**Estado verificado em 01/11/2026:** 57 testes passaram, mais nove solicitações HTTP, quatro checks de saúde e dois probes de corpus adulterado. A configuração final citou o documento esperado em 10/12 perguntas respondíveis de desenvolvimento e 12/12 da última bateria sintética. Persistem erros de relevância e ambiguidade; respostas exigem revisão.

- [Executar o projeto](projects/supportops-ai/README.md)
- [Resultados v3 e limites](projects/supportops-ai/evaluation/RESULTS_V3.md)
- [Arquitetura](projects/supportops-ai/docs/architecture.md)
- [Ponto de retomada entre sessões](CONTINUITY.md)

Os resultados incluem tentativas malsucedidas. Não há validação humana independente, uso em produção ou impacto de negócio comprovado. DemandLab continua planejado, sem implementação.
