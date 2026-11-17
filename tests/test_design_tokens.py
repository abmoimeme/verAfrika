"""Design-token contrast checks (UX standards §5.2, WCAG 1.4.3 and 1.4.11)."""
import re
from pathlib import Path

CSS = (Path(__file__).resolve().parents[1] / "web" / "app.css").read_text()
TOKENS = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", CSS))


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_brand_values_unchanged():
    assert TOKENS["navy"].upper() == "#17324D" and TOKENS["gold"].upper() == "#C9932F"
    assert TOKENS["gold-text"].upper() == "#8E6821"


def test_text_pairs_meet_4_5():
    pairs = [("text", "card"), ("text", "bg"), ("muted", "card"), ("muted", "bg"), ("gold-text", "card"),
             ("gold-text", "gold-soft"), ("navy", "gold"), ("danger", "card"), ("success", "card"), ("info", "card")]
    bad = {f"{a}/{b}": round(ratio(TOKENS[a], TOKENS[b]), 2) for a, b in pairs if ratio(TOKENS[a], TOKENS[b]) < 4.5}
    assert not bad, bad
    assert ratio("#FFFFFF", TOKENS["navy"]) >= 4.5  # header text


def test_ui_components_meet_3_to_1():
    assert ratio(TOKENS["control-border"], TOKENS["card"]) >= 3
    assert ratio(TOKENS["focus"], TOKENS["bg"]) >= 3
    assert ratio(TOKENS["gold"], TOKENS["navy"]) >= 3  # focus ring on the header


def test_gold_never_used_as_text_on_light_surfaces():
    # Rules that set `color: var(--gold)` are only allowed inside the navy header.
    offenders = [r for r in re.findall(r"([^{}]+)\{[^}]*(?<![-\w])color:\s*var\(--gold\)", CSS) if ".site-header" not in r and "background" not in r]
    assert not offenders, offenders


def test_no_text_below_12px():
    sizes = [float(x) for x in re.findall(r"font-size:\s*([\d.]+)rem", CSS)]
    assert min(sizes) * 16 >= 12, min(sizes) * 16
