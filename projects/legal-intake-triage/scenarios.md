# Scenarios for the v0 dataset

Synthetic scenarios written with Fred (2026-10-22). Each line becomes one request in `cases.jsonl`.
Fictional people and companies only. T-001 to T-010 are the reviewed provisional cases.

| # | Scenario | Expected type | Expected signals | Note |
|---|---|---|---|---|
| T-011 | Compras pede revisão de contrato de manutenção de ar-condicionado, R$ 18 mil/ano, e escreve "URGENTE!!!" | contract | — | trap: "urgente" with no real signal |
| T-012 | Cliente pede por e-mail cópia das gravações das ligações dele com o SAC "para guardar" | data_subject_rights | — | disguised data subject request |
| T-013 | RH pergunta se pode parcelar as férias de uma colaboradora em 3 períodos | labor | — | simple question |
| T-014 | Financeiro: maior cliente atrasou 3 faturas, total R$ 410 mil; pode protestar? | litigation (+ contract) | SIG-VALUE, SIG-CASH | two types |
| T-015 | Marketing quer usar depoimento de cliente em vídeo; "o CEO adorou a ideia na reunião" | advisory | — | trap: CEO mentioned, not the requester |
| T-016 | E-mail da Receita pede documentos em 20 dias, em procedimento de fiscalização | compliance | SIG-REGULATOR, SIG-HARD-DEADLINE | administrative deadline running |
| T-017 | Gerente avisa que motoboy terceirizado se acidentou na entrega e foi ao hospital | labor | SIG-LABOR-SENSITIVE | hidden urgency, casual tone |
| T-018 | Diretora comercial precisa do NDA assinado antes da reunião com investidor amanhã | contract | SIG-EXEC | |
| T-019 | Pergunta se o processo trabalhista do ex-gerente "que acabou ano passado" deixou pendência | litigation | — | trap: closed lawsuit |
| T-020 | TI: notebook de vendedor com a base de clientes foi furtado no carro | compliance | SIG-INCIDENT | incident hidden in a theft report |
