# Casos duvidosos — revisão do Fred

Casos em que a política de rotulagem (`LABELING.md`) não resolve sozinha. Para cada um: a pergunta, a proposta do autor e a sua decisão. Quando você decidir, eu ajusto `cases.jsonl` e registro a decisão no campo `note`.

**Revisado por Fred em 2026-11-05:** todas as propostas aceitas. As lacunas "fato confidencial do cliente" (C-019) e "fato de investigação interna" (C-027) ficam para a v1.

| Caso | Texto (resumo) | Pergunta e proposta do autor | Sua decisão |
|---|---|---|---|
| C-005 | Preciso de um modelo de comunicado interno. A empregada Marina Couto Prates (CPF 529.982.247-25, marina.prates… | Pergunta: o dado sensível deve ser rotulado só como 'depressão' ou como 'afastada por depressão'? Proposta do autor: só 'depressão' (o trecho mínimo que revela o dado de saúde, LGPD art. 5º, II). || De acordo com a proposta (Fred, 2026-11-05) |
| C-010 | A juíza Helena Prado Lacerda sinalizou na audiência que pode homologar um acordo rápido. Minha alçada é de até… | Pergunta: 'sinalizou que pode homologar um acordo rápido' também é estratégia (grupo 3)? Proposta do autor: não; é um fato da audiência, não a posição do cliente. Rotulados: o nome da juíza (política), o valor e a frase da alçada. || De acordo com a proposta (Fred, 2026-11-05) |
| C-017 | O teto aprovado pelo conselho para o acordo com a Distribuidora Sol Nascente é de R$ 1,2 milhão. Escreva um ro… | Pergunta: a frase inteira ('O teto aprovado pelo conselho ... é de R$ 1,2 milhão') também deve ser rotulada como clause? Proposta do autor: não; o valor já carrega o segredo e a frase não traz tese nem posição além dele. || De acordo com a proposta (Fred, 2026-11-05) |
| C-019 | Meu cliente Rafael Moreira Dias me contou que dirigia embriagado na hora do acidente. Como estruturar a defesa… | Pergunta: a confissão do cliente é grupo 3 (estratégia) ou fica fora dos grupos da v0? Proposta do autor: grupo 3, porque é o fato que a estratégia de defesa esconde; registrar como lacuna ('fato confidencial do cliente') para a v1. || De acordo com a proposta (Fred, 2026-11-05) |
| C-027 | Na investigação interna, o gerente Fábio Rocha admitiu ter recebido R$ 30 mil do fornecedor. Não vamos comunic… | Pergunta: 'admitiu ter recebido R$ 30 mil do fornecedor' deve ser rotulado (grupo 3)? Proposta do autor: não na v0; é fato confidencial da investigação, não estratégia nem negociação, e a regra de valor não se aplica (sem pista de negociação). Registrar como lacuna para a v1. || De acordo com a proposta (Fred, 2026-11-05) |
