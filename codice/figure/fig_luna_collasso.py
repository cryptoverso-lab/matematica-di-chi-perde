"""Cap. 5 — LUNA, maggio 2022: nove giorni.

Scala logaritmica, perche' su scala lineare il crollo non e' rappresentabile:
la caduta attraversa cinque ordini di grandezza e l'ultimo tratto sarebbe
indistinguibile dallo zero.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import date_italiane, firma  # noqa: E402

CAPITOLO = "sec-cap-05"
DIDASCALIA = (
    "Prezzo giornaliero di chiusura di LUNA fra aprile e giugno 2022, scala "
    "logaritmica: ogni tacca vale un fattore dieci. Dal massimo di 116 dollari del "
    "4 aprile ai 5 centesimi di millesimo del 13 maggio. Il 5 maggio valeva ancora "
    "82 dollari: sette giorni dopo ne valeva tre decimillesimi. Su scala lineare "
    "questo grafico sarebbe una linea verticale seguita da una riga piatta a zero — "
    "ed è esattamente così che i crolli appaiono a chi li guarda mentre accadono."
)


def disegna(destinazione: str = "stampa"):
    df = carica("lunausdt").filter(
        (carica("lunausdt")["data"] >= dt.date(2022, 4, 1))
        & (carica("lunausdt")["data"] <= dt.date(2022, 6, 15))
    )
    date = df["data"].to_list()
    prezzi = df["chiusura"].to_numpy()

    fig, ax = plt.subplots()
    ax.plot(date, prezzi, color="black", linewidth=1.2)
    ax.set_yscale("log")

    # Il punto del massimo sta a ridosso del bordo superiore: la sua etichetta
    # va scritta **sotto**, dove il riquadro e' vuoto, altrimenti esce dal
    # grafico. Le altre tre vanno sopra, come prima.
    # Ogni etichetta va dalla parte in cui il tracciato non passa: il massimo
    # e' a ridosso del bordo superiore, quindi la sua scritta sta sotto; il
    # minimo ha la risalita subito a destra, quindi la sua sta sotto e centrata.
    tappe = [
        (dt.date(2022, 4, 4), t("massimo\n116 $", "peak\n$116"), (6, -6), "left", "top"),
        (dt.date(2022, 5, 9), "30 $", (6, 6), "left", "bottom"),
        (dt.date(2022, 5, 11), "1,08 $", (6, 6), "left", "bottom"),
        (dt.date(2022, 5, 13), "0,00005 $", (10, -1), "left", "center"),
    ]
    for giorno, testo, scarto, orizz, vert in tappe:
        i = date.index(giorno)
        ax.plot([giorno], [prezzi[i]], marker="o", markersize=3.2, color="black")
        ax.annotate(
            testo,
            xy=(giorno, prezzi[i]),
            xytext=scarto,
            textcoords="offset points",
            fontsize=6.5,
            linespacing=1.3,
            ha=orizz,
            va=vert,
        )

    ax.set_ylabel(t("Prezzo in dollari (scala logaritmica)", "Price in dollars (log scale)"))
    ax.set_yticks([1e-4, 1e-2, 1, 100])
    ax.set_yticklabels(["0,0001", "0,01", "1", "100"])
    ax.tick_params(axis="x", labelrotation=0)
    ax.grid(which="minor", visible=False)
    date_italiane(ax, ogni_giorni=14)

    fonte, estratto = citazione("lunausdt")
    firma(fig, t(f"{fonte}, LUNAUSDT giornaliero", f"{fonte}, daily LUNAUSDT"), estratto)
    return fig
