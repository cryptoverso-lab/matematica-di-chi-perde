"""Le celle sono bilingui, e la divisione si misura sul corpus intero.

Ogni cella markdown dei 29 sorgenti porta il proprio testo inglese in coda.
Fino al piano 04-10 la coda finiva dentro `it.json`, e la pagina italiana
avrebbe mostrato un blocco inglese sotto ogni capoverso. `separa_lingue` la
toglie, e questi test presidiano le due cose che possono rompersi:

1. le DUE forme misurate — quella col marcatore e quella riconosciuta per
   impronta — danno l'italiano da una parte e l'inglese dall'altra;
2. sul corpus intero il conteggio torna: 221 celle markdown, 221 code inglesi,
   29 delle quali senza marcatore. Un numero che scende non lascia l'inglese in
   pagina: rende rosso l'ingest.

Il secondo e' il presidio vero. Il primo e' un caso; il secondo e' la regola.

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
    """Il presidio: 221 su 221. Un solo caso non riconosciuto e' un blocco
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
