"""Cap. 5 — FTT, novembre 2022: il token che ha smesso di esistere.

Non un crollo di prezzo come gli altri: qui a un certo punto il mercato si
chiude e l'ultimo prezzo diventa definitivo. E' la differenza fra un asset
che scende e un asset che finisce.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import date_italiane, firma  # noqa: E402

CAPITOLO = "sec-cap-05"
DIDASCALIA = (
    "Prezzo giornaliero di chiusura del token dell'exchange FTX, dal 1 ottobre 2022. "
    "Il 7 novembre vale 22 dollari; l'8 novembre — il giorno in cui i prelievi si "
    "bloccano — chiude a 5,50. Il 15 novembre il mercato viene chiuso e da lì in poi "
    "non esiste più un prezzo: la serie non scende verso lo zero, si interrompe. "
    "Chi aveva quel token non ha subito una perdita che poteva ancora recuperare: "
    "ha smesso di avere qualcosa."
)


def disegna(destinazione: str = "stampa"):
    df = carica("fttusdt").filter(pl.col("data") >= dt.date(2022, 10, 1))
    date = df["data"].to_list()
    prezzi = df["chiusura"].to_numpy()

    fig, ax = plt.subplots()
    ax.plot(date, prezzi, color="black", linewidth=1.3)
    ax.plot([date[-1]], [prezzi[-1]], marker="X", markersize=5, color="black")

    # I tre eventi cadono a pochi giorni l'uno dall'altro. Le etichette stanno
    # tutte nell'area vuota a sinistra, **prima** del punto a cui si
    # riferiscono, e finiscono tutte alla stessa data: così le tre frecce
    # partono in colonna e vanno tutte verso destra senza incrociarsi.
    # Le quote seguono l'ordine dei tre prezzi, e la freccia del 15 novembre
    # resta sotto il minimo della serie invece di attraversarla.
    fine_testo = dt.date(2022, 10, 24)
    for giorno, testo, quota in [
        (dt.date(2022, 11, 7), t("7 novembre: 22,08 $", "Nov 7: $22.08"), 16.0),
        (dt.date(2022, 11, 8),
         t("8 novembre: i prelievi si bloccano — 5,50 $",
           "Nov 8: withdrawals freeze — $5.50"), 9.0),
        (dt.date(2022, 11, 15),
         t("15 novembre: il mercato viene chiuso — 1,43 $",
           "Nov 15: the market is shut down — $1.43"), 0.9),
    ]:
        i = date.index(giorno)
        ax.annotate(
            testo,
            xy=(giorno, prezzi[i]),
            xytext=(fine_testo, quota),
            textcoords="data",
            fontsize=6.5,
            linespacing=1.3,
            ha="right",
            va="center",
            arrowprops=dict(arrowstyle="->", linewidth=0.7, color="black",
                            shrinkA=3, shrinkB=3),
        )

    ax.set_ylabel(t("Prezzo in dollari", "Price in dollars"))
    ax.set_ylim(0, 30)
    date_italiane(ax, ogni_giorni=7)

    fonte, estratto = citazione("fttusdt")
    firma(fig, t(f"{fonte}, FTTUSDT giornaliero fino al delisting",
                  f"{fonte}, daily FTTUSDT through delisting"), estratto)
    return fig
