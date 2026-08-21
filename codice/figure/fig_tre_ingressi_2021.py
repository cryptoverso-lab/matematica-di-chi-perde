"""Cap. 1 — Tre persone, la stessa idea, tre mesi di differenza.

E' la figura che rende personale il dato statistico: non una distribuzione, ma
tre traiettorie che si possono seguire con il dito.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-01"
INGRESSI = [
    ("2021-01-01", t("Gennaio", "January")),
    ("2021-04-01", t("Aprile", "April")),
    ("2021-11-01", t("Novembre", "November")),
]
DIDASCALIA = (
    "Tre ingressi nello stesso anno, sullo stesso asset, con la stessa strategia: "
    "comprare e tenere dodici mesi. Chi ha cominciato a gennaio 2021 si è ritrovato "
    "in utile del 63%, chi ha cominciato dieci mesi dopo in perdita del 66%. "
    "Centoventinove punti percentuali di differenza, e nessuno dei tre ha preso una "
    "sola decisione diversa dagli altri."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt")
    prezzi = df["chiusura"].to_numpy()
    date = df["data"].to_list()

    fig, ax = plt.subplots()
    tratti = ["-", "--", "-."]
    grigi = ["#000000", "#595959", "#8C8C8C"]

    for (giorno, nome), tratto, grigio in zip(INGRESSI, tratti, grigi):
        i = date.index(dt.date.fromisoformat(giorno))
        finestra = prezzi[i : i + 366]
        curva = finestra / finestra[0] * 100
        x = np.arange(len(curva))
        ax.plot(x, curva, linestyle=tratto, color=grigio, linewidth=1.1)
        ax.annotate(
            f"{nome}: {num(curva[-1] - 100, segno=True)}%",
            xy=(len(curva) - 1, curva[-1]),
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=7,
            va="center",
        )

    ax.axhline(100, color="black", linewidth=0.75, linestyle=":")
    ax.set_xlabel(t("Giorni trascorsi dall'ingresso", "Days elapsed since entry"))
    ax.set_ylabel(t("Capitale (100 = somma investita)", "Capital (100 = amount invested)"))
    ax.set_xlim(0, 460)
    ax.set_ylim(0, 260)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero", f"{fonte}, daily BTCUSDT"), estratto)
    return fig
