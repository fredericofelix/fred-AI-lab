---
title: Lex Seed · Guardrail de Sigilo
emoji: 🌱
colorFrom: yellow
colorTo: gray
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
short_description: Aponta o que pode violar o sigilo antes de enviar à IA
---

# Lex Seed · Guardrail de Sigilo

Antes de colar um texto num ChatGPT ou Copilot, passe por aqui: o guardrail aponta o que pode violar o sigilo
profissional (cliente e partes, número de processo, estratégia, marcações, informação de terceiro sob NDA, dados
pessoais), explica o fundamento e sugere substituições. Não reescreve nem envia nada.

Código, rubrica e métricas: [fred-AI-lab/projects/secrecy-guardrail](https://github.com/fredericofelix/fred-AI-lab/tree/main/projects/secrecy-guardrail).

## Privacidade

- Tudo roda dentro deste Space, sem API externa. O app não armazena nem registra o texto; os logs têm só tempos
  de processamento. Analytics, flagging e API pública estão desligados.
- O texto passa pela infraestrutura do Hugging Face, nos EUA. **Use texto fictício ou já genérico.** Para texto
  real, rode no seu computador (instruções no README do projeto).

Não constitui aconselhamento jurídico.
