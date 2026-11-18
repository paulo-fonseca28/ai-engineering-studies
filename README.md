# AI Engineering Studies

Reúno neste repositório meus estudos de engenharia de IA, com implementação, testes, documentação e evidências reproduzíveis. Desenvolvo os projetos com apoio de ferramentas de IA e mantenho os resultados e limitações registrados.

## SupportOps AI — versão 1.0

Criei o SupportOps como uma aplicação de suporte para delivery fictício. Nele, integrei busca lexical/semântica/híbrida, inferência local, respostas com fontes, estado simulado, rastros persistidos, revisão e cancelamento confirmados, autenticação configurável e integração n8n com sistema HTTP externo de teste.

- [Executar e demonstrar](projects/supportops-ai/README.md)
- [Vídeo](projects/supportops-ai/docs/demo/supportops-demo.webm)
- [Fechamento técnico e evidências](projects/supportops-ai/docs/RELEASE.md)
- [Resultados do modelo e limitações](projects/supportops-ai/evaluation/RESULTS_V3.md)
- [Artigo: recuperação, fidelidade e execução](projects/supportops-ai/docs/technical-note.md)
- [Continuidade](CONTINUITY.md)

Na validação do projeto, passaram 103 testes Python, 1 teste JavaScript e 2 testes de navegador. Também validei os fluxos HTTP e n8n com inferência local real. Os dados são sintéticos, sem validação humana independente ou impacto de negócio comprovado. A aplicação não está hospedada como serviço público; execução e empacotamento estão documentados.

## DemandLab

Planejei o DemandLab como meu próximo projeto, mas ainda não iniciei sua implementação. Vou desenvolvê-lo separadamente.

Código sob [MIT](LICENSE); dados próprios têm a licença indicada em cada projeto.
