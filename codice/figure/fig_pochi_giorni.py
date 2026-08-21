"""Cap. 9 — Tutto il risultato sta in venti giorni su 3.200.

Togliere i dieci giorni migliori e togliere i dieci peggiori: due operazioni
simmetriche con effetti opposti e violentissimi. E' la ragione per cui
"restare investiti" e "evitare i crolli" sono la stessa identica scommessa.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-09"
DIDASCALIA = (
    "Capitale finale su 3.239 giorni, togliendo dalla serie i giorni migliori oppure "
    "i giorni peggiori. Chi avesse evitato i dieci giorni peggiori avrebbe portato a "
    "casa 103 volte il capitale invece di 13,7; chi avesse mancato i dieci migliori "
    "sarebbe sceso a 2,9. Venti giorni su 3.200 — lo 0,6% del tempo — "
    "spostano il risultato di un fattore trentacinque. E nessuno sa in anticipo quali "
    "siano: nella stessa settimana di maggio 2022 ci sono sia il peggiore sia uno "
    "dei migliori."
)


def disegna(destinazione: str = "stampa"):
    r = rendimenti(carica("btcusdt")["chiusura"].to_numpy())
    ordinati = np.argsort(r)
    totale = float(np.prod(1 + r))

    quanti = [0, 5, 10, 20, 30]
    senza_peggiori, senza_migliori = [], []
    for k in quanti:
        peggiori = set(ordinati[:k].tolist())
        migliori = set(ordinati[len(r) - k:].tolist())
        senza_peggiori.append(float(np.prod([1 + v for i, v in enumerate(r) if i not in peggiori])))
        senza_migliori.append(float(np.prod([1 + v for i, v in enumerate(r) if i not in migliori])))

    fig, ax = plt.subplots()
    ax.plot(quanti, senza_peggiori, color="black", linestyle="-", linewidth=1.3,
            marker="o", markersize=3)
    ax.plot(quanti, senza_migliori, color="#8C8C8C", linestyle="--", linewidth=1.3,
            marker="s", markersize=3)
    ax.axhline(totale, color="black", linestyle=":", linewidth=0.8)

    ax.annotate(t(f"tutti i giorni: {num(totale, 1)}×", f"all days: {num(totale, 1)}×"),
                xy=(15, totale), xytext=(0, 9), textcoords="offset points", fontsize=7,
                bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none"))
    # Etichette nello spazio vuoto sopra e sotto le curve, non sui loro punti.
    riquadro = dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none")
    # Nella fascia centrale, fra le due curve: appoggiate al bordo superiore e
    # a quello inferiore finivano sotto il tratto che dovevano etichettare.
    ax.annotate(t("evitando i giorni peggiori", "avoiding the worst days"), xy=(0.96, 0.72),
                xycoords="axes fraction", fontsize=7, ha="right", va="center",
                bbox=riquadro)
    ax.annotate(t("mancando i giorni migliori", "missing the best days"), xy=(0.96, 0.27),
                xycoords="axes fraction", fontsize=7, ha="right", va="center",
                color="#595959", bbox=riquadro)

    ax.set_yscale("log")
    ax.set_xlabel(t("Giorni esclusi dalla serie", "Days excluded from the series"))
    ax.set_ylabel(t("Capitale finale (× iniziale, scala log.)", "Final capital (× starting, log scale)"))
    ax.set_yticks([1, 10, 100, 1000])
    ax.set_yticklabels(["1×", "10×", "100×", "1.000×"])
    ax.grid(which="minor", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero 2017-2026", f"{fonte}, daily BTCUSDT 2017-2026"), estratto)
    return fig
