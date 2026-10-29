# AI Engineering Studies

Estudos pessoais de engenharia de IA com implementações reproduzíveis e resultados verificáveis.

## Projetos

[SupportOps AI](projects/supportops-ai) prepara respostas para uma operação fictícia de delivery. Implementa API, recuperação lexical, fontes, rastreamento, demonstração sem credenciais e adaptador de inferência local. A avaliação tem conjuntos separados e relatórios auditáveis.

O desenvolvimento mantém código, testes e documentação juntos por entrega. Estado atual, comandos e limitações estão no README de cada projeto. Não há alegações de uso em produção ou impacto de negócio.

## Estado verificado

SupportOps AI: inferência local executada, 22 testes automatizados passando e avaliação reproduzível publicada. O baseline lexical alcançou Recall@3 de 66,7% nas 12 perguntas respondíveis do teste. A geração ainda contém erros semânticos e falhas adversariais; não está pronta para uso autônomo. Veja [evidências e limitações](projects/supportops-ai/evaluation/RESULTS.md).

Próximo incremento: comparar recuperação semântica/híbrida e medir fidelidade das respostas, usando desenvolvimento para ajustes e um novo teste reservado para validação independente.

## Incremento em andamento

Busca semântica e híbrida implementadas e comparadas no desenvolvimento. A semântica recuperou a política correta em primeiro lugar nas 12 perguntas respondíveis, mas também retornou documentos nos casos sem resposta. Veja [comparação](projects/supportops-ai/evaluation/reports/dev-retrieval-v2.md) e o README do projeto para execução.
