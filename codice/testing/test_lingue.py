"""Le celle sono bilingui, e la divisione si misura sul corpus intero.

Ogni cella markdown dei 29 sorgenti porta il proprio testo inglese in coda.
Fino al piano 04-10 la coda finiva dentro `it.json`, e la pagina italiana
avrebbe mostrato un blocco inglese sotto ogni capoverso. `separa_lingue` la
toglie, e questi test presidiano le due cose che possono rompersi:

1. le DUE forme misurate — quella col marcatore e quella riconosciuta per
   impronta — danno l'italiano da una parte e l'inglese dall'altra;
2. sul corpus intero il conteggio torna: 222 celle markdown, 222 code inglesi,
   29 delle quali senza marcatore. Un numero che scende non lascia l'inglese in
   pagina: rende rosso l'ingest.

Il secondo e' il presidio vero. Il primo e' un caso; il secondo e' la regola.

DAL PIANO 04-12 c'e' un terzo presidio, ed e' della stessa famiglia: la coda
inglese non viene piu' soltanto tolta dall'italiano, viene RESA, ed e' cio' che
riempie `en.json`. Cio' che puo' rompersi li' e' la STRUTTURA — dove l'italiano
ha un titolo, l'inglese ha un corsivo in testa, perche' dentro una citazione un
`##` non si scrive — e si presidia allo stesso modo: i due casi, piu' il
conteggio sul corpus (149 titoli rispecchiati, 29 titoli di lab).

Uso:  uv run python -m pytest codice/testing/test_lingue.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
LAB = RADICE / "codice" / "lab"
sys.path.insert(0, str(RADICE / "codice" / "src"))
sys.path.insert(0, str(LAB))

from estrazione.celle import celle_del_sorgente  # noqa: E402
from estrazione.prosa import (  # noqa: E402
    CELLA_BILINGUE_SENZA_MARCATORE,
    ProsaSconosciuta,
    converti,
    separa_lingue,
)
from estrazione.sorgente import estrai_dal_sorgente  # noqa: E402
from estrazione.sorgente import ATTESI  # noqa: E402

CON_MARCATORE = """Tre sguardi sugli stessi identici dati.

---

> **EN** — *Looking is not measuring.* Three views of the same data.
"""

SENZA_CODA = """Un capoverso italiano.

E un secondo capoverso, sempre italiano.
"""


def test_la_forma_col_marcatore_da_due_lingue() -> None:
    italiano, inglese, nuda = separa_lingue(CON_MARCATORE, "prova")
    assert italiano == "Tre sguardi sugli stessi identici dati."
    assert inglese == "*Looking is not measuring.* Three views of the same data."
    assert nuda is False
    assert "EN" not in italiano, "il marcatore resta col ramo inglese, non con l'italiano"


def test_il_separatore_resta_un_separatore_quando_non_introduce_l_inglese() -> None:
    """Un `---` seguito da prosa e' una riga di separazione, non un confine di
    lingua: la cella torna intera. E' il verso che impedisce alla divisione di
    mangiarsi un pezzo di testo italiano."""
    cella = "Prima parte.\n\n---\n\nSeconda parte, sempre italiana.\n"
    italiano, inglese, _ = separa_lingue(cella, "prova")
    assert italiano == cella
    assert inglese == ""


def test_una_cella_senza_coda_non_viene_divisa() -> None:
    italiano, inglese, nuda = separa_lingue(SENZA_CODA, "prova")
    assert (italiano, inglese, nuda) == (SENZA_CODA, "", False)


def test_la_cella_senza_marcatore_e_quella_vera_del_corpus() -> None:
    """Il ramo fragile si prova sul testo VERO, non su uno inventato: e' l'unico
    modo in cui l'impronta pinnata significhi qualcosa."""
    cella = next(
        c
        for c in celle_del_sorgente(LAB / "lab_05_misurare.py")
        if c.tipo == "markdown" and "PROVA" in c.sorgente
    )
    italiano, inglese, nuda = separa_lingue(cella.sorgente, cella.dove)
    assert nuda is True, (
        f"l'impronta pinnata {CELLA_BILINGUE_SENZA_MARCATORE} non riconosce piu' la "
        "cella «PROVA / TRY»: se il testo e' cambiato, va rimisurata"
    )
    assert "PROVA" in italiano and "NON TOCCARE" in italiano
    assert "TRY" in inglese and "DO NOT CHANGE" in inglese
    assert "TRY" not in italiano, "e' il difetto: l'inglese dentro la pagina italiana"


def test_converti_non_lascia_l_inglese_nell_html() -> None:
    resa = converti(CON_MARCATORE, "prova")
    assert resa.html == "<p>Tre sguardi sugli stessi identici dati.</p>"
    assert resa.coda_inglese.startswith("*Looking is not measuring.*")
    assert "<hr />" not in resa.html, (
        "il `---` era il confine fra le due lingue: tolto l'inglese non e' piu' "
        "una riga di separazione da rendere"
    )


def test_la_coda_inglese_non_viene_convertita() -> None:
    """Resta markdown di proposito: convertirla farebbe fallire l'ingest su un
    costrutto inglese che oggi nessuna pagina pubblica."""
    resa = converti(CON_MARCATORE, "prova")
    assert "<em>" not in resa.coda_inglese and "*" in resa.coda_inglese


@pytest.mark.lento
def test_sul_corpus_intero_ogni_cella_markdown_e_bilingue() -> None:
    """Il presidio: 222 su 222. Un solo caso non riconosciuto e' un blocco
    inglese pubblicato dentro una pagina italiana."""
    celle = 0
    con_coda = 0
    nude = 0
    for percorso in sorted(LAB.glob("lab_*.py")) + sorted(LAB.glob("calc_*.py")):
        for indice, cella in enumerate(celle_del_sorgente(percorso)):
            if cella.tipo != "markdown":
                continue
            celle += 1
            testo = cella.sorgente
            if indice == 0:
                testo = testo.split("\n", 1)[1]  # via il titolo di primo livello
            try:
                _, inglese, nuda = separa_lingue(testo, cella.dove)
            except ProsaSconosciuta as fallimento:  # pragma: no cover
                pytest.fail(str(fallimento))
            con_coda += 1 if inglese else 0
            nude += 1 if nuda else 0
    assert celle == ATTESI["code_inglesi"], "celle markdown del corpus"
    assert con_coda == ATTESI["code_inglesi"], (
        f"{celle - con_coda} celle markdown senza coda inglese riconosciuta: "
        "sono blocchi che finirebbero in pagina in due lingue"
    )
    assert nude == ATTESI["code_inglesi_nude"]


# ------------------------------------------------------------------ #
# La coda inglese diventa HTML, e tiene la struttura dell'italiano     #
# ------------------------------------------------------------------ #

CON_TITOLO = """## 1. Tre sguardi

Cambia `SERIE` e riesegui.

---

> **EN** — *1. Three views.* Change `SERIE` and rerun.
"""

CON_DOMANDA = """## 2. Vera o finta?

Sei grafici.

---

> **EN** — *2. Real or fake?* Six charts.
"""

TITOLO_SENZA_CORSIVO = """## 3. Le quattro domande

Prima di credere a un numero.

---

> **EN** — Before believing any number.
"""

def test_il_titolo_italiano_si_rispecchia_in_quello_inglese() -> None:
    """Dove l'italiano ha un `##`, l'inglese ha un corsivo in testa — e torna a
    essere un titolo dello stesso livello. Senza, la pagina inglese avrebbe la
    stessa prosa con la struttura tolta."""
    resa = converti(CON_TITOLO, "prova")
    assert resa.html.startswith("<h2>1. Tre sguardi</h2>")
    assert resa.html_en.startswith("<h2>1. Three views</h2>")
    assert resa.html_en.endswith("<p>Change <code>SERIE</code> and rerun.</p>")
    assert resa.titoli_specchio == 1
    assert "<em>" not in resa.html_en, "il corsivo era un titolo, non un corsivo"


def test_cade_il_punto_e_resta_il_punto_interrogativo() -> None:
    """«*1. Three views.*» e' una frase e il punto e' suo; «2. Real or fake?»
    senza il punto interrogativo sarebbe un'altra cosa."""
    assert converti(CON_TITOLO, "prova").html_en.startswith("<h2>1. Three views</h2>")
    assert converti(CON_DOMANDA, "prova").html_en.startswith("<h2>2. Real or fake?</h2>")


def test_un_titolo_italiano_senza_corsivo_inglese_ferma_l_ingest() -> None:
    """La prova in negativo dello specchio. Il costo di NON fermarsi e' una
    sezione che sparisce dalla pagina inglese senza che nessuno lo veda."""
    with pytest.raises(ProsaSconosciuta) as fallimento:
        converti(TITOLO_SENZA_CORSIVO, "prova")
    assert "corsivo" in str(fallimento.value)


def test_il_corsivo_che_va_a_capo_e_lo_stesso_titolo() -> None:
    """Nel corpus succede 4 volte su 149: il corsivo sta su due righe perche' la
    riga del sorgente e' finita, non perche' il titolo abbia due righe."""
    cella = (
        "## 2. Rispetto a cosa? Il confronto onesto\n\nIl confronto giusto.\n\n"
        "---\n\n> **EN** — *2. Compared to what? The honest comparison on the\n"
        "> second half.* The right comparison.\n"
    )
    resa = converti(cella, "prova")
    assert resa.html_en.startswith(
        "<h2>2. Compared to what? The honest comparison on the second half</h2>"
    )


def test_la_prima_cella_da_il_titolo_inglese_del_lab() -> None:
    """Il titolo del lab e' un campo del bundle in tutte e due le lingue: in
    italiano lo stacca `titolo_e_corpo`, in inglese e' il corsivo in testa alla
    prima coda. Se restasse nella prosa, la pagina lo mostrerebbe due volte."""
    cella = (
        "*Quaderno del capitolo «Cosa vuol dire misurare».*\n\nTre sguardi.\n\n"
        "---\n\n> **EN** — *Lab 5 — Looking is not measuring.* Notebook for the "
        "chapter. Three views.\n"
    )
    resa = converti(cella, "prova", prima_cella=True)
    assert resa.titolo_en == "Lab 5 — Looking is not measuring"
    assert "Looking is not measuring" not in resa.html_en
    assert resa.html_en.startswith("<p>Notebook for the chapter.")
    assert resa.titoli_specchio == 0, "la prima cella non rispecchia un titolo: lo DA'"


def test_la_cella_tutta_inglese_non_produce_nemmeno_il_blocco_inglese() -> None:
    """La decisione del piano 04-12 sulla voce 14 di `deferred-items.md`: quella
    cella non entra ne' in `it.json` ne' in `en.json`. Un blocco presente in una
    lingua sola costerebbe un campo di contratto, un ramo nel gate di parita' e
    un ramo nella pagina — per pubblicare la glossa di un output che la pagina
    inglese gia' dichiara di servire in italiano."""
    estrazione = estrai_dal_sorgente(LAB / "lab_21_ai.py")
    assert estrazione.prosa_solo_inglese == 1
    assert set(estrazione.prosa) == set(estrazione.prosa_en), (
        "gli identificativi devono coincidere nelle due lingue: e' la parita' "
        "che il gate del sito pretende"
    )


@pytest.mark.lento
def test_sul_corpus_intero_la_struttura_inglese_specchia_l_italiana() -> None:
    """Il presidio vero dello specchio: 149 titoli e 29 titoli di lab, contati
    sui 29 sorgenti. Un numero che scende e' una sezione che la pagina inglese
    non ha piu'."""
    specchi = 0
    titoli = 0
    blocchi_en = 0
    for percorso in sorted(LAB.glob("lab_*.py")) + sorted(LAB.glob("calc_*.py")):
        estrazione = estrai_dal_sorgente(percorso)
        specchi += estrazione.titoli_specchio
        titoli += 1 if estrazione.titolo_en else 0
        blocchi_en += len(estrazione.prosa_en)
        assert set(estrazione.prosa) == set(estrazione.prosa_en), percorso.name
    assert specchi == ATTESI["titoli_specchio"]
    assert titoli == ATTESI["titolo_en"]
    assert blocchi_en == ATTESI["code_inglesi"] - ATTESI["prosa_solo_inglese"]


# ------------------------------------------------------------------ #
# Le figure: bilingui nelle etichette, bilingui anche nei numeri       #
# ------------------------------------------------------------------ #

PROGRAMMA_FIGURE_INGLESI = """
import glob, json, os, re, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, SRC)
sys.path.insert(0, FIGURE)
import importlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cvbook.stile import contesto

# In inglese la virgola separa le migliaia: sospetta solo davanti a una o due
# cifre ("0,5") oppure a quattro o piu' ("0,0001"). "10,240" e' corretto.
sospetta = re.compile(r"[0-9],[0-9](?![0-9][0-9])|[0-9],[0-9]{4,}")

guasti = {}
for percorso in sorted(glob.glob(os.path.join(FIGURE, "fig_*.py"))):
    modulo = os.path.basename(percorso)[:-3]
    m = importlib.import_module(modulo)
    if not hasattr(m, "disegna"):
        continue
    with contesto("stampa"):
        figura = m.disegna()
    figura.canvas.draw()
    testi = [t.get_text() for t in figura.findobj(matplotlib.text.Text) if t.get_text()]
    plt.close("all")
    trovati = sorted({t for t in testi if sospetta.search(t)})
    if trovati:
        guasti[modulo] = trovati

with open(ESITO, "w", encoding="utf-8") as f:
    json.dump(guasti, f, ensure_ascii=False)
"""


def test_le_figure_in_inglese_non_stampano_numeri_all_italiana(tmp_path) -> None:
    """Con `CVBOOK_LANG=en` nessuna figura deve scrivere «0,5×».

    Le etichette erano gia' tutte dentro `t()`, ed e' per questo che il difetto
    e' passato inosservato: le parole erano inglesi e i numeri no. Ventuno
    figure su quarantatre' stampavano la virgola decimale anche in inglese,
    dove «0,062 points a day» non e' sei centesimi, e' sessantadue. Le tacche
    scritte a mano venivano da liste di stringhe italiane; quelle automatiche
    dalla locale, impostata sull'italiano una volta per tutte.

    Il gate gira in un processo a parte perche' la lingua si legge una volta
    all'importazione di `cvbook.lingua`: cambiarla dentro la sessione di pytest
    non la cambierebbe per i moduli gia' importati. E l'esito passa da un file,
    non dallo standard output, che sotto pytest 9 torna vuoto.
    """
    import json
    import os
    import subprocess

    esito = tmp_path / "esito.json"
    intestazione = "\n".join([
        f"SRC = {str(RADICE / 'codice' / 'src')!r}",
        f"FIGURE = {str(RADICE / 'codice' / 'figure')!r}",
        f"ESITO = {str(esito)!r}",
    ])
    ambiente = dict(os.environ, CVBOOK_LANG="en", PYTHONIOENCODING="utf-8")
    conclusa = subprocess.run(
        [sys.executable, "-c", intestazione + PROGRAMMA_FIGURE_INGLESI], env=ambiente
    )
    assert conclusa.returncode == 0, "il disegno delle figure in inglese e' fallito"

    guasti = json.loads(esito.read_text(encoding="utf-8"))
    assert not guasti, (
        "figure che in inglese stampano numeri all'italiana:\n  "
        + "\n  ".join(f"{nome}: {testi}" for nome, testi in guasti.items())
        + "\n\nLe tacche scritte a mano si compongono con `cvbook.stile.tacca`."
    )
