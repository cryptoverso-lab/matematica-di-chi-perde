"""L'avvio dei quaderni scarica tutto quello che i quaderni importano.

IL DIFETTO CHE QUESTO FILE ESISTE PER NON FAR RIPETERE. `codice/lab/avvio.py`
tiene un elenco scritto a mano dei moduli di `cvbook` da scaricare quando il
quaderno gira fuori dalla repository — cioe' su Colab, cioe' in mano al lettore.
Il 2026-08-21 e' nato `cvbook/lingua.py`, `cvbook/stile.py` ha cominciato a
importarlo, e nessuno l'ha aggiunto a quell'elenco. Per quattro giorni
**ventisette quaderni su ventinove** sono morti alla prima cella con
`ModuleNotFoundError: No module named 'cvbook.lingua'`.

Perche' non se ne e' accorto nessuno: sia la suite in locale sia la CI eseguono
i quaderni **dentro** il checkout, dove `cvbook` e' gia' importabile e l'elenco
di `avvio` non viene nemmeno letto. Verde ovunque, rotto per chi inquadra il QR.

La regola qui sotto e' quella che avrebbe intercettato il difetto il giorno in
cui e' nato: si parte dai moduli che i quaderni importano davvero, si segue la
catena degli import interni al pacchetto, e si pretende che l'elenco di `avvio`
copra la chiusura. Un modulo nuovo dentro `cvbook` non richiede di ricordarsi
niente: o e' irraggiungibile dai quaderni, o questo test diventa rosso.

La prova vera resta `codice/testing/prova_colab.py`, che i quaderni li esegue
per davvero in una cartella vuota con la rete. Questo test costa millisecondi e
prende lo stesso difetto: e' il gate che si puo' permettere di girare sempre.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "codice" / "lab"
CVBOOK = ROOT / "codice" / "src" / "cvbook"

sys.path.insert(0, str(LAB))

from avvio import MODULI, SERIE  # noqa: E402

#: Sorgenti che non sono quaderni: sono gli attrezzi della cartella.
NON_QUADERNI = {"avvio.py", "costruisci.py", "genera_indice.py", "estrai_bundle.py",
                "estrai_errata.py"}


def _moduli_cvbook_importati(sorgente: Path) -> set[str]:
    """I moduli di `cvbook` che questo file importa, per nome senza estensione."""
    albero = ast.parse(sorgente.read_text(encoding="utf-8"))
    trovati: set[str] = set()
    for nodo in ast.walk(albero):
        # `from cvbook.dati import serie` e `from cvbook import seed_for`
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            if nodo.module == "cvbook":
                trovati.add("__init__")
            elif nodo.module.startswith("cvbook."):
                trovati.add(nodo.module.split(".", 1)[1].split(".")[0])
            # `from .lingua import t`, dentro il pacchetto stesso
            elif nodo.level and sorgente.parent == CVBOOK:
                trovati.add(nodo.module.split(".")[0])
        # `import cvbook.stile`
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name == "cvbook":
                    trovati.add("__init__")
                elif alias.name.startswith("cvbook."):
                    trovati.add(alias.name.split(".", 1)[1].split(".")[0])
    return trovati


def _chiusura(iniziali: set[str]) -> set[str]:
    """Segue la catena degli import dentro `cvbook` finche' non aggiunge nulla."""
    visti: set[str] = set()
    da_vedere = set(iniziali) | {"__init__"}
    while da_vedere:
        nome = da_vedere.pop()
        if nome in visti:
            continue
        visti.add(nome)
        file = CVBOOK / f"{nome}.py"
        if file.exists():
            da_vedere |= _moduli_cvbook_importati(file) - visti
    return visti


def quaderni() -> list[Path]:
    return sorted(p for p in LAB.glob("*.py") if p.name not in NON_QUADERNI)


def test_i_quaderni_esistono():
    assert quaderni(), "nessun sorgente di quaderno in codice/lab/"


def test_avvio_scarica_tutto_cio_che_i_quaderni_importano():
    """Il difetto del 2026-08-21, preso alla radice invece che in mano al lettore."""
    # `avvio.py` conta come radice: e' lui a importare `cvbook.stile` per la
    # funzione `figura()`, che ogni quaderno usa senza importarla in proprio.
    richiesti = _moduli_cvbook_importati(LAB / "avvio.py")
    for quaderno in quaderni():
        richiesti |= _moduli_cvbook_importati(quaderno)

    serve = _chiusura(richiesti)
    # `seed_for` e simili sono nomi esportati da `__init__`, non moduli.
    serve = {n for n in serve if (CVBOOK / f"{n}.py").exists()}
    scaricati = {Path(m).stem for m in MODULI}

    mancanti = sorted(serve - scaricati)
    assert not mancanti, (
        "codice/lab/avvio.py non scarica moduli che i quaderni raggiungono: "
        f"{mancanti}. Su Colab il quaderno muore alla prima cella con "
        "ModuleNotFoundError, e in casa non si vede perche' cvbook e' gia' "
        "importabile. Aggiungili a MODULI."
    )


def test_avvio_non_scarica_moduli_che_nessuno_usa():
    """Il difetto opposto: peso e tempo di avvio spesi per niente.

    Non e' grave come il primo — un modulo di troppo non rompe niente — ma un
    elenco che accumula e non toglie smette di descrivere cio' che serve, e la
    prossima persona non sa piu' quali righe puo' toccare.
    """
    richiesti = _moduli_cvbook_importati(LAB / "avvio.py")
    for quaderno in quaderni():
        richiesti |= _moduli_cvbook_importati(quaderno)
    serve = {n for n in _chiusura(richiesti) if (CVBOOK / f"{n}.py").exists()}
    scaricati = {Path(m).stem for m in MODULI}

    inutili = sorted(scaricati - serve)
    assert not inutili, (
        f"codice/lab/avvio.py scarica moduli che nessun quaderno raggiunge: {inutili}"
    )


@pytest.mark.parametrize("quaderno", quaderni(), ids=lambda p: p.name)
def test_ogni_serie_chiesta_da_un_quaderno_esiste(quaderno: Path):
    """`avvio.prepara([...])` fallisce a runtime su una serie sconosciuta.

    Meglio saperlo qui che dopo trenta secondi di download, in Colab, davanti a
    un lettore che ha appena inquadrato un codice QR.
    """
    albero = ast.parse(quaderno.read_text(encoding="utf-8"))
    for nodo in ast.walk(albero):
        if (isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "prepara"
                and nodo.args
                and isinstance(nodo.args[0], ast.List)):
            for elemento in nodo.args[0].elts:
                if isinstance(elemento, ast.Constant) and isinstance(elemento.value, str):
                    assert elemento.value in SERIE, (
                        f"{quaderno.name} chiede la serie {elemento.value!r}, "
                        f"che avvio.SERIE non conosce"
                    )
