"""Lingua attiva del progetto — supporto bilingue italiano/inglese.

Il libro e le sue figure restano italiani per default: nessuna variabile
d'ambiente impostata equivale a `it`, e l'output non cambia di un pixel
rispetto a prima. Chi clona la repository da fuori Italia puo' pero' chiedere
`CVBOOK_LANG=en` e vedere le stesse figure, calcolatori e quaderni con le
etichette in inglese — utile per una repo pubblica e internazionale.
"""

from __future__ import annotations

import os

#: Valori ammessi. Qualunque altra cosa (typo, lingua non supportata, variabile
#: vuota) ricade silenziosamente su "it": una build non deve rompersi per una
#: variabile d'ambiente scritta male.
_LINGUE_AMMESSE = {"it", "en"}


def _leggi_lingua() -> str:
    grezza = os.environ.get("CVBOOK_LANG", "it").strip().lower()
    return grezza if grezza in _LINGUE_AMMESSE else "it"


#: Letta una volta all'importazione del modulo. E' cosi' che la usano tutte le
#: figure e i calcolatori: cambiarla a runtime richiede reimportare il modulo,
#: che e' esattamente cio' che succede a ogni esecuzione di uno script o di una
#: cella di un notebook.
LINGUA = _leggi_lingua()


def t(it: str, en: str) -> str:
    """Restituisce `it` o `en` a seconda della lingua attiva.

    Il default resta l'italiano: se `CVBOOK_LANG` non e' impostata, `t()` si
    comporta come l'identita' su `it` e nessuna figura del libro cambia.
    """
    return en if LINGUA == "en" else it
