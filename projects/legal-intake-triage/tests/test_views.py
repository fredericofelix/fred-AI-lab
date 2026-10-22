import json
from pathlib import Path

import pytest
import views

from triage.decide import decide, fallback
from triage.extraction import Extraction, SignalHit
from triage.pipeline import StageEvent
from triage.rubric import load_rubric
from triage.sanitize import Sanitized

ROOT = Path(__file__).resolve().parent.parent
SITE_ICON = Path.home() / "projects/lex-seed-site/public/brand/icon-robot.svg"


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


@pytest.fixture(scope="module")
def showcase(rubric):
    return decide(
        Extraction(
            "data_subject_rights",
            "pediu pra apagar tudo",
            None,
            (SignalHit("SIG-REGULATOR", "vai reclamar no Procon"),),
            "high",
            (),
        ),
        rubric,
    )


def test_copy_is_exact():
    assert views.NOTICE == (
        "⚠️ **Não cole dados reais** de clientes, colaboradores ou processos. Antes da triagem, o Detector LGPD "
        "da Privacy Seed mascara CPF, CNPJ, PIS, CNH, título de eleitor, cartão, e-mail, telefone, CEP e data de "
        "nascimento. **Nomes e endereços não são mascarados nesta versão.** O texto é processado só em memória, "
        "no Hugging Face, e não é guardado."
    )
    assert views.BANNER == "🚧 Em construção: versão de teste."
    assert views.DISCLAIMER == (
        "**Triagem automatizada de demandas jurídicas.** Demonstração com dados sintéticos: um modelo de IA aberto "
        "identifica o tipo e os sinais da demanda, e regras explícitas (a rubrica) definem prioridade e prazo. "
        "A ferramenta pode errar; casos de risco alto ou incertos vão para revisão humana. "
        "Esta ferramenta não constitui aconselhamento jurídico."
    )
    assert views.CTA == (
        "Quer aplicar ao seu jurídico, com a sua régua e os seus canais (e-mail, Slack, Teams)? "
        "[Fale com a Lex Seed](https://www.lexseed.com.br/?utm_source=hf-space&utm_medium=space"
        "&utm_campaign=triagem-juridica)."
    )


def test_no_copy_promises_anonymization():
    for text in (views.NOTICE, views.DISCLAIMER, views.CTA, views.SANITIZE_LIMIT):
        assert "anonimiz" not in text.lower()


def test_validate_input():
    assert views.validate_input("") == views.EMPTY_INPUT == "Cole uma demanda ou escolha um exemplo."
    assert views.validate_input("   \n ") == views.EMPTY_INPUT
    assert views.validate_input("Revisar contrato") is None


def test_steps_html_marks_done_and_current():
    html = views.steps_html([StageEvent("sanitize", True, "1 CPF mascarado"), StageEvent("extract", False, "")], True)
    assert 'class="step done"' in html and "1 CPF mascarado" in html
    assert 'class="step now"' in html
    assert html.count('class="step next"') == 2
    assert "Detector LGPD by Privacy Seed" in html
    # The official icon inlined as a data URI: no static-file route to configure in the Space.
    assert "data:image/svg+xml;base64," in html and "robot thinking" in html


def test_steps_html_stops_robot_when_finished():
    events = [StageEvent(s, True, "") for s in ("sanitize", "extract", "check", "decide")]
    html = views.steps_html(events, False)
    assert "robot thinking" not in html and html.count('class="step done"') == 4


def test_sanitize_html_shows_what_was_masked_and_the_limit():
    html = views.sanitize_html(Sanitized("CPF [CPF], CNPJ 11.222.333/0001-81", {"[CPF]": 1}, {"[CNPJ]": 1}))
    assert "Passo 1" in html and "Detector LGPD by Privacy Seed" in html
    assert "1 CPF" in html and "CNPJ" in html and "sinalizado" in html
    assert "CPF [CPF]" in html
    assert views.SANITIZE_LIMIT in html
    assert "huggingface.co/spaces/fred-ai-lab/detector-lgpd" in html


def test_sanitize_html_escapes_visitor_text():
    html = views.sanitize_html(Sanitized("<script>alert(1)</script>", {}, {}))
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_result_html_for_showcase(showcase, rubric):
    html = views.result_html(showcase, rubric)
    for needle in ("LGPD / direitos do titular", "Alta", "2 dias úteis", "15 dias", "LGPD, art. 19, II", "risco alto"):
        assert needle in html


def test_result_html_for_fallback(rubric):
    html = views.result_html(fallback(rubric), rubric)
    assert "saída do modelo inválida" in html and "mesmo dia" not in html


def test_why_rows(showcase):
    rows = views.why_rows(showcase)
    assert rows[0] == ["data_subject_rights", "pediu pra apagar tudo", showcase.fired[0].effect]
    assert rows[1] == ["SIG-REGULATOR", "vai reclamar no Procon", "risco → alto"]


def test_rubric_tables(rubric):
    types, signals = views.rubric_tables(rubric)
    assert len(types) == 8 and len(signals) == 9
    assert types[0][0] == "Contratos"


def test_examples_load_and_rebuild_results(rubric):
    examples = views.load_examples(ROOT / "space" / "examples.json")
    assert examples and examples[0]["id"] == "T-001"
    run = views.example_run(examples[0], rubric)
    assert run.decision.legal_deadline_days == 15
    assert json.dumps(examples)  # plain JSON, no objects


def test_robot_icon_is_byte_copy():
    if not SITE_ICON.exists():
        pytest.skip("lex-seed-site not checked out")
    assert (ROOT / "assets" / "icon-robot.svg").read_bytes() == SITE_ICON.read_bytes()
