"""Cap. 4 — Il gestore che indovina dieci volte di fila.

Se mandi previsioni opposte a due meta' di una lista e ogni volta tieni solo
chi ha ricevuto quella giusta, dopo dieci giri esiste un gruppo di persone per
cui hai indovinato dieci volte su dieci. Non hai previsto nulla: hai selezionato.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-04"
PARTENZA = 10_240
GIRI = 10
DIDASCALIA = (
    "Da 10.240 destinatari iniziali, mandando a metà di essi una previsione e "
    "all'altra metà quella opposta, e proseguendo ogni volta solo con chi ha ricevuto "
    "quella risultata corretta, restano dieci persone per cui il mittente ha indovinato "
    "dieci volte su dieci. Nessuna previsione è stata fatta: è stata fatta una "
    "selezione. Chi guarda solo il gruppo finale vede un veggente; chi guarda l'intera "
    "lista vede l'aritmetica."
)


def disegna(destinazione: str = "stampa"):
    giri = np.arange(GIRI + 1)
    rimasti = PARTENZA / 2.0**giri

    fig, ax = plt.subplots()
    ax.step(giri, rimasti, where="post", color="black", linewidth=1.2)
    ax.plot(giri, rimasti, linestyle="none", marker="o", markersize=2.6, color="black")

    for g in (0, 3, 6, 10):
        ax.annotate(
            num(rimasti[g]),
            xy=(g, rimasti[g]),
            xytext=(3, 5),
            textcoords="offset points",
            fontsize=6.5,
        )

    ax.annotate(
        t("per queste dieci persone\nil mittente ha indovinato\ndieci volte su dieci",
          "for these ten people\nthe sender has been right\nten times out of ten"),
        xy=(10, 10),
        xytext=(1.5, 40),
        textcoords="data",
        fontsize=6.5,
        linespacing=1.35,
        arrowprops=dict(arrowstyle="->", linewidth=0.6, color="#595959"),
    )

    ax.set_yscale("log")
    ax.set_xlabel(t("Previsioni inviate", "Predictions sent"))
    ax.set_ylabel(t("Destinatari ancora convinti (scala log.)", "Recipients still convinced (log scale)"))
    ax.set_xticks(range(0, GIRI + 1, 2))
    ax.set_yticks([10, 100, 1000, 10000])
    ax.set_yticklabels(["10", "100", "1.000", "10.000"])
    ax.grid(which="minor", visible=False)

    firma(fig, t("aritmetica elementare, nessun dato di mercato",
                  "basic arithmetic, no market data"), "—")
    return fig
