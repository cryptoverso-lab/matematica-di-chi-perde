"""Cap. 7 — Due modi di guadagnare con i mercati.

A parita' di bravura dichiarata, quanto rende operare e quanto rende insegnare
a operare. Non e' un'accusa: e' un conto che chiunque puo' rifare, e spiega
perche' l'offerta formativa sia cosi' abbondante.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-07"
PREZZO_CORSO = 497
RESA = 0.30  # rendimento annuo dichiarato, molto generoso
DIDASCALIA = (
    "Ricavo annuo di due attività diverse. La linea continua è quanto produce "
    "operare sui mercati con un rendimento del 30% annuo — una cifra che quasi "
    "nessun gestore professionale sostiene nel tempo — al variare del capitale "
    "disponibile. La linea tratteggiata è quanto produce vendere un corso da 497 "
    "euro, al variare del numero di iscritti. Con 20.000 euro di capitale e una "
    "bravura eccezionale si arriva a 6.000 euro l'anno; con 200 iscritti, quasi "
    "centomila. La differenza non dice nulla sull'onesta' di nessuno: dice dove "
    "sono i soldi, e quindi dove va l'offerta."
)


def disegna(destinazione: str = "stampa"):
    capitale = np.array([5_000, 10_000, 20_000, 50_000, 100_000, 200_000])
    ricavo_trading = capitale * RESA

    iscritti = np.array([10, 25, 50, 100, 200, 400])
    ricavo_corso = iscritti * PREZZO_CORSO

    fig, ax = plt.subplots()
    x = np.arange(len(capitale))

    ax.plot(x, ricavo_trading, color="black", linestyle="-", linewidth=1.3,
            marker="o", markersize=3)
    ax.plot(x, ricavo_corso, color="#595959", linestyle="--", linewidth=1.3,
            marker="s", markersize=3)

    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{c//1000}k\n{i}" for c, i in zip(capitale, iscritti)], fontsize=6.5
    )
    ax.set_xlabel(t("sopra: capitale investito (€)   ·   sotto: iscritti al corso",
                     "top: capital invested (€)   ·   bottom: course enrollees"), fontsize=7)
    ax.set_ylabel(t("Ricavo annuo (€)", "Annual revenue (€)"))
    ax.set_yscale("log")
    ax.set_yticks([1000, 10_000, 100_000])
    ax.set_yticklabels(["1.000", "10.000", "100.000"])
    ax.grid(which="minor", visible=False)

    ax.text(0.03, 0.94, t("vendere un corso da 497 €", "selling a €497 course"), transform=ax.transAxes,
            fontsize=7, color="#595959", va="top")
    ax.text(0.03, 0.87, t("operare al 30% annuo", "trading at 30% a year"), transform=ax.transAxes,
            fontsize=7, color="black", va="top")

    firma(fig, t("calcolo diretto, prezzo di corso da listini pubblici",
                  "direct calculation, course price from public listings"), "—")
    return fig
