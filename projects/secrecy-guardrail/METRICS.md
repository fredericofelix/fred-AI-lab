# Métricas da v0

40 textos fictícios no estilo "advogado pedindo ajuda a uma IA" (30 com pontos sigilosos, 10 limpos), em
[`cases.jsonl`](cases.jsonl), com as regras de rotulagem em [`LABELING.md`](LABELING.md). Modelo: híbrido
(GLiNER2 para empresas, Qwen3-4B para estratégia e informação de terceiro), rodando localmente.

**Limites desta medição:** conjunto pequeno, escrito e rotulado pelo autor do projeto; Fred Gomes revisou os 5 casos
duvidosos. A lista de nomes genéricos ignorados (`generic_names`) foi ajustada nesses mesmos casos. Leia os números
como sinal de direção, não como garantia.

## Resultado

| Métrica | Valor |
|---|---|
| **Recall nos grupos 1, 2, 4 e 5** (não deixar passar o que é sigiloso) | **98%** (meta: 90%) |
| Casos limpos com algum alarme | 0 de 10 |
| Precisão (apontamentos que correspondem a um rótulo) | 84% |
| Tempo por texto no Hugging Face (CPU gratuita, modelos carregados) | 18 a 24 s |

| Grupo | Recall | Precisão |
|---|---|---|
| 1 · Identidade de cliente ou parte | 100% | 83% |
| 2 · Número de processo (CNJ) | 100% | 100% |
| 3 · Estratégia e negociação (**experimental**) | 63% | 60% |
| 4 · Marcação de confidencialidade | 100% | 100% |
| 5 · Informação de terceiro sob NDA ou segredo industrial | 86% | 100% |
| 6 · Dados pessoais (Detector LGPD) | 100% | 90% |

Só regras fixas e o Detector LGPD, sem o modelo, chegam a 63% de recall nos grupos 1, 2, 4 e 5: o modelo
acrescenta os nomes de empresas e o conteúdo recebido sob confidencialidade.

## Onde erra

- **Teses sem palavra de negociação** (grupo 3): "Nossa tese principal será a prescrição bienal", "vamos sustentar
  a decadência do crédito de 2018", "vamos segurar a proposta até a audiência" (C-003, C-011, C-029). Por isso o
  grupo é experimental.
- **Informação de terceiro sem nenhuma pista** (grupo 5): o roadmap recebido "em caráter reservado" (C-012). Quando
  há pista ("NDA", "segredo industrial", "acordo de confidencialidade"), a pista é sempre apontada e, nos casos
  medidos, o conteúdo também.
- **Fatos confidenciais do cliente** que não são estratégia (a confissão em C-019, o fato da investigação em C-027)
  não cabem nos seis grupos da v0. Lacuna registrada para a v1.
- **Alarmes a mais:** o Detector LGPD marca um ano sozinho ("2023") como data de nascimento (achado repassado à
  Privacy Seed); nomes de juízes e advogados da outra parte são apontados de propósito (a v0 não sabe quem é o cliente).

Números brutos: [`metrics/v1-hybrid.json`](metrics/v1-hybrid.json) e [`metrics/v1-rules-only.json`](metrics/v1-rules-only.json).
Escolha do modelo e tempos: [`SPIKE.md`](SPIKE.md).
