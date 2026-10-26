## Métricas da v0

**40 demandas sintéticas** de jurídico interno, escritas e rotuladas com um advogado (Fred), incluindo casos difíceis de propósito: pedidos de titular disfarçados, urgência escondida ("nada urgente"), dois tipos possíveis e armadilhas ("URGENTE!!!" sem nada urgente, valor logo abaixo do limite, processo já encerrado).

Modelo: Qwen3-4B (aberto, Apache-2.0), rodando em CPU. Arquivos brutos em `metrics/`.

### Métrica principal: a triagem deixa passar o que é grave?

| | v0 inicial | + checagem do valor | + dicas na rubrica | Meta |
|---|---|---|---|---|
| **Casos graves pegos** (classificados como graves ou enviados a humano) | 88% | 88% | **94%** | ~90–95% |
| Revisão humana por incerteza do modelo | 7,5% | 7,5% | **7,5%** | ≤ 30% |
| Revisão humana por regra (todo risco alto) | 47,5% | 42,5% | 45% | reportada |
| Tipo correto | 77,5% | 77,5% | **85%** | — |
| Sinais encontrados | 79% | 79% | **86%** | — |
| Prioridade correta | 72,5% | 77,5% | **82,5%** | — |
| Saída válida | 95% | 95% | **97,5%** | — |

"Grave" = risco alto ou prioridade crítica pela rubrica (17 dos 40 casos).

### O que mudou entre as versões

1. **Checagem do valor por código.** O sinal "valor acima de R$ 50 mil" só vale se o trecho citado trouxer um valor maior que o limite da rubrica. Eliminou falsos positivos em contratos de R$ 18 mil e R$ 49 mil.
2. **Dicas na rubrica.** "Carta do fórum" conta como prazo fatal mesmo que digam que não é urgente; multa, atraso e rescisão contam como impacto no caixa; e uma regra geral: *julgue pelos fatos, não pelo tom de quem escreve*.

### Onde ainda erra

- **1 caso grave escapou:** aluguel que renova sozinho com multa de 3 aluguéis, escrito como "pergunta rápida, sem pressa". O modelo viu o vencimento, não viu a multa.
- **Pedidos da diretoria feitos por terceiros** ("o CEO pediu", "aqui é a assistente do CFO") às vezes não são reconhecidos.
- **Excesso de cautela:** uma dúvida simples sobre multa do FGTS foi lida como trabalhista sensível; o resultado vai para revisão humana, sem risco.

### Onde a rubrica e o advogado discordam

Um caso: cliente avisa que vai rescindir um contrato de R$ 300 mil e cobrar multa de 20%. A rubrica dá **Normal (5 dias)**; o advogado daria **Alta (2 dias)**. Régua padrão sempre deixa escapar algo: ajustar a rubrica à realidade de cada jurídico é parte do trabalho.

### Tempo

No Hugging Face (CPU gratuita, 2 vCPUs): cerca de 25–40 s por demanda com o modelo carregado; até ~3 min na primeira demanda depois de um tempo sem uso.

### Limites

Dados sintéticos; 40 casos; um único anotador nesta versão; nomes e endereços não são mascarados. Não constitui aconselhamento jurídico.
