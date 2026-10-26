---
title: Lex Seed · Triagem Jurídica
emoji: 🌱
colorFrom: yellow
colorTo: gray
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
short_description: Triagem de demandas jurídicas com rubrica auditável
---

# Lex Seed · Triagem Jurídica

Demonstração do módulo [`legal-intake-triage`](https://github.com/fredericofelix/fred-AI-lab/tree/main/projects/legal-intake-triage) do Fred AI Lab: um modelo de IA aberto identifica o tipo e os sinais de risco de uma demanda do jurídico interno, e uma rubrica editável define prioridade e prazo. Dados sintéticos.

## Privacidade desta demonstração

- **Uso recomendado:** não cole dados reais. Para dados reais, rode o projeto localmente.
- **Saneamento:** antes da triagem, a biblioteca [`privacyseed-lgpd`](https://github.com/fredericofelix/privacyseed-lgpd) (Privacy Seed) mascara CPF, CNPJ (sinalizado), PIS, CNH, título de eleitor, cartão, e-mail, telefone, CEP e data de nascimento. Nomes e endereços não são mascarados.
- **O que a demonstração faz:** processa o texto apenas em memória, com um modelo que roda dentro do Space (nenhuma API externa). Não há registro, armazenamento, flagging ou analytics do texto, e a função não é listada na documentação da API nem pode ser chamada pelos clientes Gradio.
- **Papel de agente:** se a LGPD se aplicar a esta demonstração gratuita (é discutível que haja tratamento com fins econômicos), o responsável pelo Fred AI Lab atua como controlador do tratamento efêmero, por definir sua finalidade e seus meios, e o Hugging Face como operador (LGPD, art. 5º, VI e VII).
- **Base legal:** legítimo interesse (art. 7º, IX, e art. 10), com minimização garantida pelo aviso, pelo saneamento e pela ausência de persistência.
- **Transferência internacional:** a infraestrutura do Hugging Face fica fora do Brasil (art. 33). A [política de privacidade do Hugging Face](https://huggingface.co/privacy) informa que seus servidores ficam nos Estados Unidos.
- **Limite:** os registros de infraestrutura do próprio Hugging Face (como IP e metadados de requisição) estão fora do controle desta demonstração.

Não constitui aconselhamento jurídico. Quer aplicar ao seu jurídico? [Fale com a Lex Seed](https://www.lexseed.com.br/?utm_source=hf-space&utm_medium=space&utm_campaign=triagem-juridica).
