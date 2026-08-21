"""La composizione del bundle: cio' che l'ingest produce e cio' che TIENE.

Un solo argomento, e vale il file a parte. `lab.json` e i blocchi di `it.json`
li produce questa catena e si possono ricomporre da zero a ogni giro; l'apparato
delle figure — `alt`, `didascalia`, `metodo` — no: lo scrive una persona nel
repo del sito guardando la figura (UI-SPEC 3.4, LAB-03). Fino al piano 04-10
`bundle.py` ricomponeva `it.json` con un `"figure": {}` letterale, e ogni testo
alternativo scritto a mano aveva la vita di una riesecuzione.

Questi test non eseguono nessun quaderno e non aprono nessun sorgente: guardano
la sola fusione. Stanno in un file proprio e non in `test_estrazione.py` per la
ragione scritta nella voce 7 delle voci rinviate del sito — quel file chiude a
543 righe, ed e' la divisione a dover venire prima dell'aggiunta, non dopo. Qui
il criterio e' *di che cosa parla il test*: la composizione del bundle, non
l'estrazione dal sorgente.

Uso:  uv run python -m pytest codice/testing/test_bundle.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE / "codice" / "src"))
sys.path.insert(0, str(RADICE / "codice" / "lab"))

from estrazione.bundle import figure_conservate  # noqa: E402
from estrazione.comune import ProblemaDiIngest  # noqa: E402

#: L'apparato di una figura come lo scrive una persona: tre campi, tutti
#: editoriali. Non e' una forma inventata per il test — e' quella dei due
#: `alt` del pilota gia' committati in `content/labs/l05/it.json`.
APPARATO = {
    "alt": "Tre pannelli affiancati sugli stessi 3 240 giorni di btcusdt.",
    "didascalia": "Gli stessi dati guardati in tre modi.",
    "metodo": "Variazioni giornaliere in percentuale, chiusura su chiusura.",
}


def _scrivi_it(tmp_path: Path, figure: dict | None) -> Path:
    prosa: dict = {"titolo": "Lab 5", "domanda": "Che cosa vuol dire misurare?", "blocchi": []}
    if figure is not None:
        prosa["figure"] = figure
    percorso = tmp_path / "it.json"
    percorso.write_text(json.dumps(prosa, ensure_ascii=False, indent=2), encoding="utf-8")
    return percorso


def test_un_alt_scritto_a_mano_sopravvive_alla_riesecuzione(tmp_path: Path) -> None:
    """Il difetto misurato, in positivo: e' la ragione per cui esiste il file."""
    percorso = _scrivi_it(tmp_path, {"c03-1": APPARATO})
    tenute = figure_conservate(percorso, ["c03-1"])
    assert tenute == {"c03-1": APPARATO}, (
        "il testo alternativo e' lavoro editoriale: ricomporre `it.json` da zero "
        "lo cancella, e lo cancella in silenzio"
    )


def test_la_figura_che_il_quaderno_non_emette_piu_non_sopravvive(tmp_path: Path) -> None:
    """Il filtro, che e' la meta' meno ovvia della fusione.

    Senza, l'apparato di una figura tolta dal quaderno resterebbe nel bundle per
    sempre: e' precisamente il residuo che un ingest esiste per non produrre.
    """
    percorso = _scrivi_it(tmp_path, {"c03-1": APPARATO, "c99-1": APPARATO})
    tenute = figure_conservate(percorso, ["c03-1"])
    assert list(tenute) == ["c03-1"]


def test_l_ordine_e_quello_delle_figure_prodotte(tmp_path: Path) -> None:
    """Due esecuzioni di fila devono scrivere lo stesso byte (D-06)."""
    percorso = _scrivi_it(tmp_path, {"c04-1": APPARATO, "c03-1": APPARATO})
    assert list(figure_conservate(percorso, ["c03-1", "c04-1"])) == ["c03-1", "c04-1"]


def test_il_primo_giro_non_ha_niente_da_tenere(tmp_path: Path) -> None:
    """Un lab mai estratto prima: nessun file, nessun apparato, nessun errore."""
    assert figure_conservate(tmp_path / "it.json", ["c03-1"]) == {}


def test_un_it_json_senza_apparato_non_e_un_errore(tmp_path: Path) -> None:
    """I 28 bundle prodotti prima di questa correzione hanno `figure` vuoto o
    assente: rifiutarli renderebbe la correzione un blocco della catena."""
    assert figure_conservate(_scrivi_it(tmp_path, None), ["c03-1"]) == {}
    assert figure_conservate(_scrivi_it(tmp_path, {}), ["c03-1"]) == {}


def test_un_it_json_illeggibile_FERMA_l_ingest(tmp_path: Path) -> None:
    """Un JSON rotto non si sovrascrive alla cieca.

    E' il caso in cui il file c'e' ma non si riesce a leggerlo: proseguire
    significherebbe cancellare l'apparato proprio quando non lo si e' potuto
    guardare. L'errore nomina il file.
    """
    percorso = tmp_path / "it.json"
    percorso.write_text('{"titolo": "Lab 5", "figure": {', encoding="utf-8")
    with pytest.raises(ProblemaDiIngest) as fallimento:
        figure_conservate(percorso, ["c03-1"])
    assert "it.json" in str(fallimento.value)
