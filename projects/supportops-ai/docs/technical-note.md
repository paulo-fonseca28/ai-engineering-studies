# Recuperar a fonte certa não garante uma resposta fiel

O SupportOps começou com seis políticas sintéticas e busca lexical. Nas 12 perguntas respondíveis de desenvolvimento, o baseline recuperou o documento esperado em primeiro lugar em 6 casos. Embeddings Qwen3 0.6B chegaram a 12/12; a combinação RRF chegou a 11/12 no primeiro resultado e 12/12 entre os três primeiros. Esses números são específicos do conjunto pequeno e das representações usadas, não um ranking universal de estratégias.

A recuperação melhorou, mas a geração livre continuou produzindo afirmações inadequadas. Houve resposta sobre reembolso para uma pergunta de item faltante e uma resposta de astronomia acompanhada de uma política de delivery. Todas podiam satisfazer o esquema JSON e citar IDs existentes. Um contrato sintático não prova que a afirmação é sustentada.

A solução adotada limita a tarefa do modelo: escolher uma referência curta, esclarecer ou recusar. A aplicação converte a referência para o ID original e renderiza a política aprovada literalmente. Hashes impedem que documentos alterados sejam silenciosamente aceitos; um limiar calibrado em desenvolvimento bloqueia parte da evidência fraca. Isso torna a preservação do texto verificável, mas não elimina erros de relevância.

A bateria final anterior teve a política esperada em 12/12 perguntas respondíveis, porém ainda citou políticas irrelevantes em 2/6 casos sem resposta e não esclareceu 2/3 ambiguidades. Esses erros permanecem publicados. Dados, perguntas e revisão assistida foram produzidos no desenvolvimento; não há validação humana independente. Todas as partições públicas já foram expostas.

A aplicação final separa linguagem e execução. O modelo não escolhe IDs, não altera pedidos e não declara reembolso. Estado vem de uma ferramenta validada; cancelamento exige proposta, versão do registro, validade e confirmação explícita. SQLite confirma estado e recibo na mesma transação. O workflow n8n preserva a identidade de eventos para reenviar após falha do destino sem duplicar registros. Esses testes comprovam propriedades de engenharia, não compreensão geral do modelo.

A conclusão prática é manter evidências distintas: qualidade de recuperação, fidelidade do texto, relevância da seleção e correção das operações. Melhorar uma delas não autoriza presumir as outras.

[Comparação e falhas v2](../evaluation/RESULTS_V2.md) · [Seleção restrita v3](../evaluation/RESULTS_V3.md) · [Verificação da aplicação](RELEASE.md).
