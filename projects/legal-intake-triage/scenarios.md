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
| T-021 | Fornecedor do ERP avisa que o contrato renova sozinho em 10 dias, R$ 96 mil/ano, reajuste de 12% | contract | SIG-EXPIRY, SIG-VALUE | |
| T-022 | Gestor pergunta se pode pedir para a equipe trabalhar no feriado de 15/11 | labor | — | simple question |
| T-023 | Ex-colaborador pede "declaração com todos os dados que a empresa tem sobre mim" para usar em processo | data_subject_rights (+ labor) | — | two types; disguised data subject request |
| T-024 | Sócio minoritário quer sair; o CEO pediu parecer sobre apuração de haveres até sexta | corporate | SIG-EXEC | |
| T-025 | "Vocês indicam um bom contador para a minha declaração de IR pessoal?" | other | — | not a company legal matter |
| T-026 | Gerente quer instalar câmera na sala de descanso dos funcionários "por segurança" | labor (+ advisory) | — | ambiguous |
| T-027 | Procon autuou uma loja por preço divergente na gôndola, 10 dias para defesa | compliance | SIG-REGULATOR, SIG-HARD-DEADLINE | |
| T-028 | Contrato com agência de eventos para a festa de fim de ano, R$ 49 mil | contract | — | trap: value just under R$ 50 mil |
| T-029 | Recepção: "chegou uma carta do fórum para a empresa, deixei na mesa do jurídico, nada urgente" | litigation | SIG-HARD-DEADLINE | hidden urgency (service of process) |
| T-030 | Cliente pede correção do endereço, já pediu 2 vezes, vai postar no Reclame Aqui | data_subject_rights | SIG-REGULATOR | public complaint counts (Fred, rubric updated) |
| T-031 | Produto precisa dos termos de uso e política de privacidade do app novo, que lança na terça | contract (+ compliance) | SIG-LAUNCH | two types |
| T-032 | "Só para registro": cliente vai rescindir contrato de R$ 300 mil por descumprimento de SLA, multa de 20% | contract | SIG-VALUE, SIG-CASH | hidden urgency |
| T-033 | Colaborador pediu demissão e pergunta se recebe a multa do FGTS | labor | — | |
| T-034 | Candidata a vaga pede para apagar o currículo do banco de talentos | data_subject_rights | — | |
| T-035 | Canal de ética: denúncia de que vendedor oferece "agrado" a comprador de cliente público | compliance | SIG-REGULATOR | serious wrongdoing counts (Fred, rubric updated) |
| T-036 | Marketing quer escrever "o melhor café de BH" na embalagem | advisory | — | |
| T-037 | "O que muda para a gente com a reforma tributária?" | advisory | — | |
| T-038 | Assistente do CFO: "ele quer saber ainda hoje se pode assinar as procurações digitalmente" | corporate | SIG-EXEC | request on behalf of the board |
| T-039 | "Podemos usar imagem gerada por IA no site?" | advisory | — | |
| T-040 | "Quem reserva a sala de reunião do 3º andar?" | other | — | |
