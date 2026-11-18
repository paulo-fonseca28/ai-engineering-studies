# AI Engineering Studies

Estudos pessoais de engenharia de IA com implementação, testes, documentação e evidências reproduzíveis.

## SupportOps AI — versão 1.0

Aplicação de suporte para delivery fictício: busca lexical/semântica/híbrida, inferência local, respostas com fontes, estado simulado, rastros persistidos, revisão e cancelamento confirmados, autenticação configurável e integração n8n com sistema HTTP externo de teste.

- [Executar e demonstrar](projects/supportops-ai/README.md)
- [Vídeo](projects/supportops-ai/docs/demo/supportops-demo.webm)
- [Fechamento técnico e evidências](projects/supportops-ai/docs/RELEASE.md)
- [Resultados do modelo e limitações](projects/supportops-ai/evaluation/RESULTS_V3.md)
- [Artigo: recuperação, fidelidade e execução](projects/supportops-ai/docs/technical-note.md)
- [Continuidade](CONTINUITY.md)

103 testes Python, 1 teste JavaScript e 2 testes de navegador passaram. Fluxos HTTP e n8n foram executados com inferência local real. Os dados são sintéticos, sem validação humana independente ou impacto de negócio comprovado. A aplicação não está hospedada como serviço público; execução e empacotamento estão documentados.

## DemandLab

Planejado, ainda não iniciado. Será desenvolvido separadamente após o fechamento do SupportOps.

Código sob [MIT](LICENSE); dados próprios têm a licença indicada em cada projeto.
