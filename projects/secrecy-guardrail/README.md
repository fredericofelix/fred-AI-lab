# Guardrail de sigilo profissional antes do prompt

**Demo:** [Lex Seed · Guardrail de Sigilo](https://huggingface.co/spaces/fred-ai-lab/guardrail-sigilo) · Feito pela [Lex Seed](https://www.lexseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=guardrail-sigilo) · [English below](#english)

## O problema

Advogados já colam peças, e-mails e minutas no ChatGPT, no Copilot e em ferramentas parecidas. A Recomendação
CFOAB nº 001/2024 pede que o sigilo seja preservado ao inserir informações em sistemas de IA e que se evitem
detalhes que identifiquem o cliente. Falta uma ferramenta para o momento exato em que o texto vai ser enviado.

## O que esta demo faz

Você cola o texto que ia mandar para a IA. O guardrail **aponta** o que pode violar o sigilo profissional,
**explica o motivo e o fundamento** e **sugere uma substituição** (`[EMPRESA 1]`, `[PROCESSO 1]`, `[VALOR 1]`).
Ele nunca reescreve sozinho e nunca envia nada: a decisão é sua.

| Grupo | Exemplo | Como detecta |
|---|---|---|
| 1 · Identidade de cliente ou parte | "Maria Souza", "Construtora Alfa" | Detector LGPD (pessoas) + modelo (empresas) |
| 2 · Número de processo (CNJ) | `0001234-34.2025.8.13.0024` | Regra fixa com dígito verificador |
| 3 · Estratégia e negociação (**experimental**) | "aceita fechar até R$ 200 mil", "vamos alegar prescrição" | Regra fixa (valores) + modelo |
| 4 · Marcação de confidencialidade | "CONFIDENCIAL", "segredo de justiça" | Regra fixa |
| 5 · Informação de terceiro sob NDA | "conforme o NDA", a fórmula recebida | Regra fixa (pistas) + modelo |
| 6 · Dados pessoais | CPF, e-mail, telefone, dado de saúde | [Detector LGPD da Privacy Seed](https://github.com/fredericofelix/privacyseed-lgpd) |

```
texto → Detector LGPD → regras fixas → modelo de IA (lê o texto com processos e identificadores já mascarados)
      → junção (a IA só acrescenta, nunca remove o que as regras acharam) → apontamentos + prévia
```

Tudo roda localmente: GLiNER2 para empresas e [Qwen3-4B](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF)
para estratégia e informação de terceiro (ambos Apache-2.0), sem API paga e sem chamada externa.

## Resultado (v0)

40 textos fictícios (30 com pontos sigilosos, 10 limpos).

| Métrica | v0 |
|---|---|
| **Recall nos grupos 1, 2, 4 e 5** (não deixar passar o que é sigiloso) | **93%** |
| Casos limpos com alarme | 0 de 10 |
| Estratégia e negociação (experimental) | 63% |
| Tempo por texto (CPU gratuita do Hugging Face) | 18–24 s |

Erros e limites: [`METRICS.md`](METRICS.md). Escolha do modelo: [`SPIKE.md`](SPIKE.md). Segurança: [`SECURITY.md`](SECURITY.md).

## Rode no seu computador (para texto real)

Na demo pública, use só texto fictício ou já genérico. Para texto real, rode localmente: nada sai da sua máquina
(Python 3.10+; os modelos, cerca de 3,5 GB, baixam na primeira vez).

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu   # PyTorch só CPU, menor
pip install -r requirements-local.txt
python -m guardrail.eval --model none     # regras fixas + Detector LGPD, sem o modelo
python -m guardrail.eval --model hybrid   # conjunto completo nos casos rotulados
cd space && PYTHONPATH=.. python app.py   # interface em http://127.0.0.1:7860
```

## Adapte ao seu jurídico

Edite o [`rubric.yaml`](rubric.yaml): grupos, fundamentos, marcações, pistas de NDA e negociação, substituições
e nomes genéricos a ignorar. O que a versão aberta não faz, e a Lex Seed implementa: usar a sua lista real de
clientes e processos, calibrar à sua prática e integrar às suas ferramentas de IA (extensão de navegador,
Copilot, gateway).

## Limites

- Conjunto pequeno, fictício, escrito e rotulado pelo autor; Fred Gomes revisou os casos duvidosos.
- A v0 não sabe quem é o cliente: aponta todas as pessoas e empresas, inclusive juízes e advogados da outra parte.
- Teses sem palavra de negociação e informação de terceiro sem a palavra NDA escapam com frequência.
- "Nenhum ponto encontrado" não é garantia. Não constitui aconselhamento jurídico.

**Quer aplicar ao seu jurídico? [Fale com a Lex Seed](https://www.lexseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=guardrail-sigilo).**

Código sob Apache-2.0; `rubric.yaml` e `cases.jsonl` sob CC-BY-4.0.

---

## English

**Professional-secrecy guardrail before the prompt.** Paste the text you were about to send to an AI tool; the
guardrail flags what may breach professional secrecy under Brazilian law (client and party identity, CNJ case
numbers, strategy and negotiation, confidentiality markings, third-party information under NDA, personal data),
explains the legal basis and suggests a replacement. It never rewrites or sends anything. Fixed rules and the
Privacy Seed LGPD detector run first, and a local model (GLiNER2 + Qwen3-4B, no external API) can only add flags.

v0 on 40 synthetic Brazilian Portuguese texts: 93% recall on groups 1, 2, 4 and 5, no false alarms on 10 clean
texts, 63% on the experimental strategy group, 18–24 s per text on a free CPU. Limits: small author-labeled set,
no client/party distinction, "no flags" is not a guarantee, not legal advice. Run it locally for real text.

Code under Apache-2.0; rubric and cases under CC-BY-4.0. Built by [Lex Seed](https://www.lexseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=guardrail-sigilo).
