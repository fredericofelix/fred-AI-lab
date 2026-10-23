# Triagem jurídica com rubrica auditável

**Demo:** [Lex Seed · Triagem Jurídica](https://huggingface.co/spaces/fred-ai-lab/triagem-juridica) · Feito pela [Lex Seed](https://www.lexseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=triagem-juridica) · [English below](#english)

## O problema

No jurídico interno de uma pequena ou média empresa, as demandas chegam por e-mail, Slack, WhatsApp e corredor. Alguém precisa ler cada uma, entender o que é e decidir o que vem primeiro. O critério costuma ficar na cabeça dessa pessoa: ninguém consegue auditar por que um contrato esperou uma semana e outro saiu no mesmo dia.

## O que esta demo faz

Duas peças que funcionam juntas:

1. **Classificação.** Um modelo de IA aberto e pequeno ([Qwen3-4B](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF), Apache-2.0), rodando no próprio servidor, sem API paga, lê a demanda e identifica o **tipo** (contratos, trabalhista, LGPD, contencioso…) e os **sinais de risco**, sempre citando o trecho exato do texto.
2. **Rubrica auditável.** Um arquivo legível, [`rubric.yaml`](rubric.yaml), define urgência, risco, prioridade e prazo. **O modelo nunca decide o prazo:** regras fixas decidem, e cada resultado mostra qual regra disparou e por quê.

Antes de qualquer IA ler o texto, o **[Detector LGPD da Privacy Seed](https://github.com/fredericofelix/privacyseed-lgpd)** mascara identificadores (CPF, e-mail, telefone e outros).

```
demanda → Detector LGPD (mascara) → modelo (tipo + sinais + trechos) → conferência (regras existem? trechos estão no texto? valor passa do limite?) → rubrica (prioridade e prazo)
```

Risco alto, regras de exceção (citação, incidente com dados) e qualquer dúvida do modelo vão para **revisão humana**.

## Resultado (v0)

40 demandas sintéticas, escritas e rotuladas com um advogado, com casos difíceis de propósito.

| Métrica | v0 |
|---|---|
| **Casos graves pegos** (classificados como graves ou enviados a humano) | **94%** |
| Revisão humana por incerteza do modelo | 7,5% |
| Prioridade correta | 82,5% |
| Tempo por demanda (CPU gratuita) | ~25–40 s |

Detalhes, erros e evolução: [`METRICS.md`](METRICS.md). Escolha do modelo: [`SPIKE.md`](SPIKE.md).

## Adapte ao seu jurídico

A régua padrão não é a sua. Edite o [`rubric.yaml`](rubric.yaml): tipos, sinais, o limite de valor (`min_value`), a matriz urgência × risco e os prazos. Para rodar localmente (Python 3.10+):

```bash
pip install -r requirements.txt llama-cpp-python gradio==6.30.0
python -m triage.eval --model gold          # confere a rubrica com os casos rotulados
python -m triage.eval --model qwen3-4b      # roda o modelo (baixa ~2,5 GB na primeira vez)
cd space && PYTHONPATH=.. python app.py     # interface local
```

## Limites

- Dados sintéticos; 40 casos; um único anotador nesta versão.
- Nomes e endereços **não** são mascarados (o núcleo leve do detector não os detecta).
- O modelo erra: ~1 em cada 17 casos graves escapou na v0. Por isso a revisão humana é parte do fluxo, não um extra.
- Não constitui aconselhamento jurídico.

**Quer aplicar ao seu jurídico, com a sua régua e os seus canais (e-mail, Slack, Teams)? [Fale com a Lex Seed](https://www.lexseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=triagem-juridica).**

Código sob Apache-2.0; `rubric.yaml` e `cases.jsonl` sob CC-BY-4.0.

---

## English

**Legal intake triage with an auditable rubric.** A small open model (Qwen3-4B, running locally on CPU, no paid API) reads an in-house legal request and extracts its type and risk signals, each backed by a verbatim quote. Deterministic rules in an editable `rubric.yaml` set urgency, risk, priority and deadline; the model never does. The Privacy Seed detector masks identifiers before any model reads the text, and high-risk or uncertain requests go to a human.

v0 on 40 synthetic, lawyer-labeled Brazilian Portuguese requests: 94% of serious cases caught (flagged as serious or sent to a human), 7.5% sent to a human for model uncertainty, 82.5% correct priority, ~25–40 s per request on a free CPU. Limits: synthetic data, 40 cases, single annotator, names and addresses not masked, not legal advice.

Code under Apache-2.0; rubric and cases under CC-BY-4.0. Built by [Lex Seed](https://www.lexseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=triagem-juridica).
