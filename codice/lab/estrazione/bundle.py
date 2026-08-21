"""Una rotta diventa `lab.json` piu' `it.json`.

E' il punto in cui i pezzi si compongono: le celle, la prosa, i dataset e — dal
piano 04-08 — gli output e le figure di un'esecuzione vera. I percorsi che
finiscono nel bundle sono RELATIVI al repository del codice: Colab, `raw` e la
pagina del repository si compongono a render, in un solo modulo del sito
(D-14).
"""

from __future__ import annotations

from cvbook.link import ROTTE

from . import ROOT
from .comune import (
    ProblemaDiIngest,
    byte_normalizzati,
    impronta_etichettata,
    normalizza,
)
from .dataset import provenienza_delle_serie
from .sorgente import Estrazione, estrai_dal_sorgente

def bundle_di_rotta(rotta, versione: int, eseguito: str) -> tuple[dict, dict, Estrazione]:
    """`lab.json` (e, dal piano 04-07 Task 2, `it.json`) di una rotta.

    I percorsi che finiscono nel bundle sono RELATIVI al repo del libro: la URL
    di Colab, quella dei file grezzi e quella della pagina del repository si
    compongono a render, in un solo modulo del sito (D-14). Un percorso
    assoluto della macchina di build qui dentro sarebbe, oltre che inutile, un
    dettaglio di infrastruttura pubblicato (ASVS V7).
    """
    relativo_py = f"codice/lab/{rotta.file}"
    relativo_ipynb = relativo_py.replace(".py", ".ipynb")
    percorso_py = ROOT / relativo_py
    percorso_ipynb = ROOT / relativo_ipynb

    if not percorso_ipynb.is_file():
        raise ProblemaDiIngest(
            f"{rotta.file}: manca il quaderno `{relativo_ipynb}`.\n"
            "  I `.ipynb` sono artefatti di build e non stanno in git (D-15): "
            "si producono con\n"
            "  `uv run python codice/lab/costruisci.py`."
        )

    testo_py = normalizza(percorso_py.read_text(encoding="utf-8"))
    testo_ipynb = normalizza(percorso_ipynb.read_text(encoding="utf-8"))

    estrazione = estrai_dal_sorgente(percorso_py)

    lab = {
        "versione": versione,
        "codice": rotta.codice.lower(),
        "sorgente": relativo_py,
        "quaderno": relativo_ipynb,
        "eseguito": eseguito,
        "impronteSorgente": {
            "py": impronta_etichettata(testo_py),
            "ipynb": impronta_etichettata(testo_ipynb),
        },
        "dimensioni": {
            "py": byte_normalizzati(testo_py),
            "ipynb": byte_normalizzati(testo_ipynb),
        },
        "dataset": estrazione.dataset,
        "provenienza": provenienza_delle_serie(estrazione.dataset, percorso_py),
        "blocchi": estrazione.blocchi,
    }

    prosa = {
        "titolo": estrazione.titolo or rotta.titolo,
        "domanda": rotta.descrizione,
        "blocchi": estrazione.prosa,
        "figure": {},
    }

    return lab, prosa, estrazione


def rotte_scelte(filtro: str | None) -> list:
    """Le rotte da lavorare, filtrate per nome del sorgente.

    Il filtro NON entra mai in un percorso di filesystem: si confronta con i
    nomi che `cvbook.link` dichiara, e un nome sconosciuto e' un errore che
    elenca quelli buoni. Un argomento che diventasse un percorso permetterebbe
    a `--lab ../../qualcosa` di decidere che file aprire.
    """
    tutte = list(ROTTE.values())
    if filtro is None:
        return tutte
    voluto = filtro if filtro.endswith(".py") else f"{filtro}.py"
    scelte = [r for r in tutte if r.file == voluto]
    if not scelte:
        disponibili = ", ".join(sorted(r.file.removesuffix(".py") for r in tutte))
        raise ProblemaDiIngest(
            f"lab sconosciuto: `{filtro}`.\n  Disponibili: {disponibili}"
        )
    return scelte
