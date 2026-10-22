## Como funciona

1. **Saneamento (Detector LGPD by Privacy Seed).** Antes de qualquer IA ler a demanda, o [Detector LGPD](https://huggingface.co/spaces/fred-ai-lab/detector-lgpd) mascara identificadores como CPF, e-mail e telefone. Nomes e endereços não são mascarados nesta versão.
2. **Leitura (modelo aberto).** Um modelo de IA aberto e pequeno (Qwen3-4B), rodando aqui mesmo no Space, sem API paga, identifica o **tipo** da demanda e os **sinais** de risco da rubrica, sempre citando o trecho exato do texto.
3. **Conferência.** O código confere se cada regra citada existe na rubrica e se cada trecho aparece no texto. Se não, o modelo tenta mais uma vez; se falhar de novo, a demanda vai para revisão humana.
4. **Decisão (regras, não IA).** Urgência, risco, prioridade e prazo saem da rubrica, por regras fixas: o mesmo sinal gera sempre o mesmo prazo. O modelo nunca decide o prazo.

Risco alto, casos de exceção (citação, incidente de dados) e qualquer dúvida do modelo vão para **revisão humana**.

A rubrica é um arquivo editável (`rubric.yaml`): a régua de prioridades e prazos de um jurídico real é diferente desta, e ajustá-la é o primeiro passo para usar a triagem de verdade.
