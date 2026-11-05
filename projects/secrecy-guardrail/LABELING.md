# Guia de rotulagem — `cases.jsonl`

Os casos são textos **fictícios**, escritos como um advogado escreveria para uma ferramenta de IA
(resumir um caso, redigir uma resposta, revisar uma cláusula, preparar uma negociação). Nomes, empresas,
CPFs e números de processo são inventados; os números CNJ têm dígito verificador calculado.

Quem rotulou: o autor do projeto (assistente de IA, sob a direção de Fred Gomes). Os casos marcados
`doubtful` foram revisados por Fred, e a decisão dele é a que vale (campo `note`).

## Formato

Uma linha JSON por caso: `id`, `text`, `labels` (lista de `{group, kind, span}`), `clean`, `doubtful`, `note`.
Cada `span` aparece literalmente no texto. `clean: true` ⇔ nenhum rótulo.

## Regras

1. **O rótulo segue a política do guardrail**, não a opinião sobre o caso. Tudo o que a ferramenta deve
   apontar é positivo: nomes de juízes e advogados da outra parte, números de precedentes públicos,
   qualquer empresa citada. A v0 não sabe quem é o cliente.
2. **Grupos e tipos (`kind`)**:
   - 1 `person` (pessoa física) ou `org` (empresa ou organização). Nome de pessoa é sempre grupo 1, mesmo
     que o Detector LGPD o encontre.
   - 2 `cnj`: número de processo, com ou sem pontuação.
   - 3 `amount`: valor de acordo, proposta, teto ou alçada. 3 `clause`: a **menor frase** que revela tese,
     estratégia, posição de negociação ou limite de autorização.
   - 4 `marking`: "confidencial", "privilegiado", "sigiloso", "segredo de justiça" e similares.
   - 5 `third_party`: informação recebida de terceiro sob confidencialidade. Rotule a informação e,
     separadamente, a pista ("NDA", "acordo de confidencialidade") quando houver.
   - 6 `personal`: os demais dados pessoais (CPF, e-mail, telefone, endereço, data de nascimento, dado sensível).
3. **Aninhamento**: rótulos de grupos diferentes podem se sobrepor (um nome dentro de uma frase de estratégia
   conta nos dois grupos). Um valor dentro de uma frase de estratégia recebe `amount` **e** a frase recebe `clause`.
4. **Casos limpos** não contêm nada do item 1: perguntas jurídicas em abstrato, textos já genéricos
   ("[CLIENTE]", "empresa X").
5. **Duvidoso** (`doubtful: true`): quando a política não resolve o rótulo (o trecho é estratégia ou só
   contexto? o dado é sensível?). O `note` traz a pergunta e a proposta do autor; depois da revisão, a decisão de Fred.

## Como o eval conta

Um apontamento acerta um rótulo quando os trechos se sobrepõem e o grupo é o mesmo. Métrica principal:
recall nos grupos 1, 2, 4 e 5; o grupo 3 (experimental) é reportado à parte. Alarme falso: casos limpos com
algum apontamento, e a precisão sobre todos os apontamentos.
