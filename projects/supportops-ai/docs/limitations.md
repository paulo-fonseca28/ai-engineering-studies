# Limitações

- Seis documentos e 42 perguntas sintéticas; não há generalização ou impacto de negócio comprovados.
- Busca lexical não entende sinônimos e pode recuperar evidência irrelevante por coincidência de termos.
- IDs existentes e documentos esperados não garantem fidelidade semântica; métricas automáticas não substituem revisão.
- Prompt e JSON Schema não constituem defesa comprovada contra prompt injection. Os casos atuais atacam pela pergunta; ataques em documentos ainda estão pendentes.
- Teste e desenvolvimento têm perguntas distintas, mas paráfrases das mesmas políticas. Após observar o teste, mudanças exigem novo conjunto reservado para estimativa independente.
- Temperatura zero e seed fixa não garantem resultados idênticos entre versões/hardware. Latências locais não representam produção.
- Modo demo é extrativo e não entra na avaliação de qualidade de LLM. Revisão solicitada não é encaminhamento executado.
- API local sem autenticação, persistência, controle de concorrência ou integração externa. `/health` não valida o provedor.
- Dependências fixadas para o ambiente Python 3.12; outras plataformas ainda não verificadas. Docker e CI remoto pendentes.
- Hash identifica versão; histórico depende do Git. Sem retenção persistente de rastros de API.

## Falhas observadas no baseline v1

A inferência real apresentou contradição sobre cancelamento e afirmou atualização de endereço em um ataque pela pergunta. Nenhuma ação foi executada. Estes erros passaram pela validação de IDs e ocorreram com revisão sinalizada. Consulte [o relatório](../evaluation/RESULTS.md); o modelo não está validado para uso autônomo.
