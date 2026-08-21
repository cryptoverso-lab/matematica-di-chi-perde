"""Cap. prezzo e tempo — Un movimento ha due misure, non una.

Un tratto di mercato con gli estremi segnati. Ogni movimento fra due estremi
porta con se' due numeri: di quanto si e' spostato il prezzo e quanti giorni ci
ha messo. La figura ne quota uno per far vedere che sono due grandezze
indipendenti da leggere, non una sola.
"""

from __future__ import annotations

import sys
from pathlib import Path

import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.ciclica import SOGLIA, movimenti  # noqa: E402
from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t as tr  # noqa: E402
from cvbook.stile import firma, mesi_italiani, num  # noqa: E402

CAPITOLO = "sec-cap-ciclica"
DA, A = "2023-01-01", "2023-06-30"
DIDASCALIA = (
    "Bitcoin nel primo semestre del 2023, con gli estremi riconosciuti da una "
    "regola sola: un estremo diventa definitivo quando il prezzo si è allontanato "
    "del 5% nella direzione opposta. Fra un estremo e il successivo c'è un "
    "movimento, e ogni movimento porta due numeri: di quanto si è spostato il "
    "prezzo e quanti giorni ci ha messo. Il movimento quotato ne è un esempio. "
    "La regola riconosce un estremo solo dopo l'inversione: serve a descrivere "
    "movimenti finiti, non a segnalarne uno che comincia."
)


def _tratto():
    df = carica("btcusdt").sort("data")
    df = df.filter(pl.col("data").is_between(dt.date.fromisoformat(DA),
                                             dt.date.fromisoformat(A)))
    return df["data"].to_numpy(), df["chiusura"].to_numpy().astype(float)


def disegna(destinazione: str = "stampa"):
    date, prezzi = _tratto()
    tratti = movimenti(prezzi, SOGLIA)
    estremi = sorted({i for coppia in tratti for i in coppia})

    fig, ax = plt.subplots(figsize=(4.25, 4.25 * 0.52))
    ax.plot(date, prezzi, linewidth=0.8, color="#9E9E9E", linestyle="-",
            solid_joinstyle="round")
    ax.plot(date[estremi], prezzi[estremi], linewidth=1.2, color="black",
            linestyle="-", marker="o", markersize=2.6, markerfacecolor="white",
            markeredgewidth=0.8)

    # Il movimento da quotare: il piu' ampio del tratto, cosi' le due quote
    # hanno spazio e la figura resta leggibile a 4,25 pollici.
    a, b = max(tratti, key=lambda t: abs(np.log(prezzi[t[1]] / prezzi[t[0]])))
    p0, p1 = prezzi[a], prezzi[b]
    variazione = p1 / p0 - 1.0
    giorni = int((date[b] - date[a]) / np.timedelta64(1, "D"))

    # Quota verticale: quanto. Spostata a destra del vertice, con due linee di
    # richiamo: sopra il vertice la punta della freccia sparirebbe sotto il
    # pallino, e la quota sembrerebbe una freccia sola rivolta in giu'.
    import numpy as _np

    scarto = _np.timedelta64(9, "D")
    x_quota = date[b] + scarto
    for y in (p0, p1):
        ax.plot([date[b] if y == p1 else date[a], x_quota], [y, y],
                linewidth=0.5, color="#B0B0B0", linestyle="-", zorder=0)
    ax.annotate("", xy=(x_quota, p1), xytext=(x_quota, p0),
                arrowprops=dict(arrowstyle="<->", linewidth=0.75, color="black",
                                shrinkA=0, shrinkB=0))
    ax.annotate(
        f"{tr('quanto', 'how much')}: {num(variazione, 0, segno=True, percento=True)}",
        xy=(x_quota, (p0 + p1) / 2), xytext=(5, 0),
        textcoords="offset points", fontsize=6.5, va="center", ha="left")

    # Quota orizzontale: quanto a lungo.
    base = min(prezzi) * 0.945
    ax.annotate("", xy=(date[b], base), xytext=(date[a], base),
                arrowprops=dict(arrowstyle="<->", linewidth=0.75, color="black",
                                shrinkA=0, shrinkB=0))
    ax.annotate(
        tr(f"quanto a lungo: {giorni} giorni", f"how long: {giorni} days"),
        xy=(date[a] + (date[b] - date[a]) / 2, base), xytext=(0, 3),
        textcoords="offset points", fontsize=6.5, ha="center", va="bottom")

    for x, y in ((date[a], p0), (date[b], p1)):
        ax.plot([x], [y], marker="o", markersize=4.2, markerfacecolor="black",
                markeredgecolor="black")

    ax.set_ylabel(tr("Bitcoin (dollari)", "Bitcoin (dollars)"))
    ax.set_ylim(base * 0.98, max(prezzi) * 1.10)
    mesi_italiani(ax, ogni_mesi=1)
    ax.grid(axis="x", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, tr(f"{fonte}, chiusure giornaliere", f"{fonte}, daily closes"), estratto)

    disegna.numeri = {
        "movimenti_nel_tratto": len(tratti),
        "soglia": SOGLIA,
        "quotato_variazione": float(variazione),
        "quotato_giorni": giorni,
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} {v}")
