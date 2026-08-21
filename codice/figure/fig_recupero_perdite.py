"""Figura pilota — l'asimmetria fra perdita e recupero.

E' la prima figura prodotta dal progetto e serve anche da collaudo della
pipeline: nessun dato esterno, solo aritmetica. Se questa esce leggibile in
scala di grigi a 4,25 pollici, la gabbia regge.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from cvbook.lingua import t

CAPITOLO = "sec-cap-02"
DIDASCALIA = (
    "Quanto serve guadagnare per tornare al punto di partenza, dopo una perdita. "
    "La relazione non è simmetrica: perdere il 50% impone di raddoppiare per "
    "pareggiare, perdere il 90% impone di fare dieci volte il capitale rimasto. "
    "E' il motivo per cui evitare le perdite grandi vale più che cercare i guadagni grandi."
)


def disegna(destinazione: str = "stampa"):
    perdita = np.arange(2, 82, 1) / 100
    recupero = perdita / (1 - perdita)

    fig, ax = plt.subplots()
    ax.plot(perdita * 100, recupero * 100, color="black", linestyle="-", linewidth=1.3)

    # Riferimento: la retta della simmetria ingenua ("perdo 50, recupero 50").
    ax.plot(
        perdita * 100,
        perdita * 100,
        linestyle=":",
        color="#8C8C8C",
        linewidth=0.9,
    )

    ax.text(
        22, 250, t("quello che serve\nper pareggiare", "what it takes\nto break even"),
        fontsize=7, color="black", ha="center", linespacing=1.3,
    )
    ax.text(
        66, 18, t("quello che\nsi crede che serva", "what people\nthink it takes"),
        fontsize=7, color="#595959", ha="center", linespacing=1.3,
    )

    # Etichette a sinistra del punto: non attraversano mai la curva, che sale.
    for p, dx, dy in ((0.20, -6, 6), (0.50, -6, 6), (0.80, -8, -4)):
        r = p / (1 - p)
        ax.plot([p * 100], [r * 100], marker="o", markersize=3.2, color="black")
        ax.annotate(
            f"−{p:.0%} → +{r:.0%}",
            xy=(p * 100, r * 100),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=7,
            ha="right",
            va="center",
        )

    ax.set_xlabel(t("Perdita subita (%)", "Loss taken (%)"))
    ax.set_ylabel(t("Guadagno necessario per pareggiare (%)", "Gain needed to break even (%)"))
    ax.set_xlim(0, 85)
    ax.set_ylim(0, 430)
    ax.set_yticks([0, 100, 200, 300, 400])

    return fig
