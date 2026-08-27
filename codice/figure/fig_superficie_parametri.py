"""Cap. 18 — La superficie dei parametri, dentro e fuori campione.

Il valore migliore trovato ottimizzando non e' un punto stabile: spostato di
poco cambia molto, e sui dati mai visti la mappa e' diversa. Un picco isolato
e' un avvertimento, non una scoperta.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.regole import esegui, sopra_media  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-18"
FINESTRE = np.arange(5, 121, 5)
COSTO = 0.0012
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Risultato della stessa regola al variare del suo unico parametro, la "
    "lunghezza della media. La linea continua è calcolata sulla prima metà "
    "della storia, quella tratteggiata sulla seconda. Il valore che vince "
    "nella prima metà non è quello che vince nella seconda, e la forma stessa "
    "delle due curve è diversa. Con un solo parametro il problema è già "
    "visibile; con cinque diventa invisibile, perché nessuno può disegnare "
    "una mappa a cinque dimensioni."
)


def _risultato(p: np.ndarray, finestra: int) -> float:
    """Regola e costi vengono da `cvbook.regole`: un solo motore per tutto."""
    return esegui(p, sopra_media(p, finestra), costo=COSTO)["finale"]


def disegna(destinazione: str = "stampa"):
    p = carica("btcusdt").sort("data")["chiusura"].to_numpy()
    meta = len(p) // 2

    dentro = [_risultato(p[:meta], f) for f in FINESTRE]
    fuori = [_risultato(p[meta:], f) for f in FINESTRE]

    fig, ax = plt.subplots()
    ax.plot(FINESTRE, dentro, color="black", linestyle="-", linewidth=1.3,
            marker="o", markersize=2.6)
    ax.plot(FINESTRE, fuori, color="#8C8C8C", linestyle="--", linewidth=1.3,
            marker="s", markersize=2.6)

    i_best = int(np.argmax(dentro))
    ax.axvline(FINESTRE[i_best], color="#595959", linestyle=":", linewidth=0.9)
    ax.annotate(
        t(f"il migliore sulla prima metà:\n{FINESTRE[i_best]} giorni",
          f"the best on the first half:\n{FINESTRE[i_best]} days"),
        xy=(FINESTRE[i_best], max(dentro)),
        xytext=(8, -6),
        textcoords="offset points",
        fontsize=6.5,
        linespacing=1.3,
    )

    ax.text(0.62, 0.22, t("prima metà (ottimizzata)", "first half (optimized)"),
            transform=ax.transAxes, fontsize=7)
    ax.text(0.62, 0.14, t("seconda metà (mai vista)", "second half (never seen)"),
            transform=ax.transAxes, fontsize=7, color="#595959")

    ax.set_xlabel(t("Lunghezza della media (giorni)", "Moving average length (days)"))
    ax.set_ylabel(t("Capitale finale (× iniziale)", "Final capital (× starting)"))
    ax.set_yscale("log")

    i_fuori = int(np.argmax(fuori))
    disegna.numeri = {
        "migliore_dentro_finestra": int(FINESTRE[i_best]),
        "migliore_dentro_valore": dentro[i_best],
        "stessa_finestra_fuori": fuori[i_best],
        "migliore_fuori_finestra": int(FINESTRE[i_fuori]),
        "migliore_fuori_valore": fuori[i_fuori],
        "compra_e_tieni_totale": float(p[-1] / p[0]),
        "compra_e_tieni_fuori": float(p[-1] / p[meta]),
    }

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT — costi dello 0,12% per operazione inclusi",
                  f"{fonte}, BTCUSDT — 0.12% per trade included"), estratto)
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:28s} {v}")
