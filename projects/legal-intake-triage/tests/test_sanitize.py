from fakes import cnpj, cpf

from triage.sanitize import sanitize


def test_masks_cpf_and_email_and_counts_them():
    s = sanitize(f"Cliente CPF {cpf()}, e-mail cliente@exemplo.com, pediu exclusão.")
    assert "[CPF]" in s.text and "[EMAIL]" in s.text
    assert cpf() not in s.text and "cliente@exemplo.com" not in s.text
    assert s.masked == {"[CPF]": 1, "[EMAIL]": 1}


def test_cnpj_is_flagged_not_masked():
    s = sanitize(f"Fornecedor CNPJ {cnpj()} mandou a minuta.")
    assert cnpj() in s.text
    assert s.flagged == {"[CNPJ]": 1}
    assert s.masked == {}


def test_clean_text_unchanged():
    text = "Preciso revisar o contrato com o fornecedor até sexta."
    s = sanitize(text)
    assert s.text == text and s.masked == {} and s.flagged == {}


def test_health_words_are_kept():
    assert sanitize("acidente de trabalho com afastamento").text == "acidente de trabalho com afastamento"
