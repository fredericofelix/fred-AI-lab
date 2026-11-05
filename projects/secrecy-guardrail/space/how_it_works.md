## Como funciona

1. **Dados pessoais — Detector LGPD by Privacy Seed.** A biblioteca aberta
   [`privacyseed-lgpd`](https://github.com/fredericofelix/privacyseed-lgpd) encontra nomes de pessoas, CPF,
   e-mail, telefone, endereço e dados sensíveis.
2. **Regras fixas.** Números de processo no padrão CNJ (com checagem do dígito verificador), marcações como
   "confidencial" e "segredo de justiça", valores perto de palavras de negociação ("acordo", "teto", "alçada") e
   pistas de NDA. A IA não consegue remover o que as regras encontram.
3. **Modelo de IA aberto, rodando aqui mesmo.** Procura empresas, estratégia e informação de terceiro sob
   confidencialidade. Ele lê o texto com os números de processo e os identificadores já trocados por marcadores,
   e cada trecho que aponta precisa aparecer literalmente no texto.
4. **Prévia.** A mesma entidade recebe sempre o mesmo rótulo (`[EMPRESA 1]`, `[PESSOA 1]`, `[PROCESSO 1]`).
   Teses e marcações são só sinalizadas: trocar a frase inteira deixaria o texto inútil.

Nenhuma chamada a API externa. O app não guarda nem registra o texto. Se o modelo falhar ou demorar demais, a
tela avisa que a verificação por IA não foi concluída: nunca mostra um resultado "limpo" nesse caso.

**Fundamentos.** Estatuto da Advocacia (Lei 8.906/94), art. 7º, II, e art. 34, VII; Código de Ética e Disciplina
da OAB, arts. 35 a 38; Recomendação CFOAB nº 001/2024 (uso de IA generativa na advocacia); Lei 9.279/96,
art. 195, XI; LGPD, art. 5º, I e II.
