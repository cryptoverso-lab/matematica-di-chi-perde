"""Cap. 6 — La funzione del valore percepito.

Il dolore di una perdita non e' il rovescio del piacere di un guadagno della
stessa misura: e' circa il doppio. La forma di questa curva e' il risultato
sperimentale piu' replicato dell'economia comportamentale, e spiega da sola
meta' degli errori operativi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-06"
ALFA = 0.88   # curvatura, dai lavori sperimentali originali
LAMBDA = 2.25  # quanto pesa di piu' una perdita rispetto a un guadagno pari
DIDASCALIA = (
    "Valore soggettivo attribuito a un guadagno e a una perdita della stessa entita', "
    "secondo i parametri stimati sperimentalmente dalla teoria del prospetto. "
    "Guadagnare 1.000 euro produce una soddisfazione; perderne 1.000 produce un "
    "dispiacere circa due volte e mezzo più grande. La curva è anche più piatta "
    "verso l'esterno: la differenza fra perdere 8.000 e perderne 10.000 si sente molto "
    "meno di quella fra perdere zero e perderne 2.000. E' il motivo per cui, dopo una "
    "perdita già grande, rischiare ancora costa poco in termini di dolore atteso."
)


def disegna(destinazione: str = "stampa"):
    x = np.linspace(-10, 10, 400)
    # np.where valuta entrambi i rami: si eleva il valore assoluto e si rimette
    # il segno dopo, per non calcolare la potenza frazionaria di un negativo.
    grandezza = np.abs(x) ** ALFA
    v = np.where(x >= 0, grandezza, -LAMBDA * grandezza)

    fig, ax = plt.subplots()
    ax.plot(x, v, color="black", linewidth=1.3)
    ax.axhline(0, color="black", linewidth=0.75)
    ax.axvline(0, color="black", linewidth=0.75)

    g = 3.0
    vg = g**ALFA
    vp = -LAMBDA * g**ALFA
    for valore, testo, va in (
        (vg, t(f"guadagno {g:.0f}", f"gain {g:.0f}"), "bottom"),
        (vp, t(f"perdita {g:.0f}", f"loss {g:.0f}"), "top"),
    ):
        segno = 1 if valore > 0 else -1
        ax.plot([segno * g, segno * g], [0, valore], linestyle=":", color="#595959", linewidth=0.9)
        ax.plot([0, segno * g], [valore, valore], linestyle=":", color="#595959", linewidth=0.9)
        ax.annotate(testo, xy=(segno * g, valore), xytext=(6 * segno, 0),
                    textcoords="offset points", fontsize=7,
                    ha="left" if segno > 0 else "right", va="center")

    # Sotto il ramo delle perdite, non accanto: a meta' altezza il testo si
    # estende verso destra fin dove la curva risale, e ci finisce sotto.
    ax.annotate(
        t("il dolore è circa\n2,5 volte il piacere", "the pain is about\n2.5 times the pleasure"),
        xy=(-9.4, vp * 2.35),
        fontsize=7,
        linespacing=1.35,
        va="center",
        bbox=dict(boxstyle="square,pad=0.2", facecolor="white", edgecolor="none"),
    )

    ax.set_xlabel(t("Esito monetario (migliaia di euro)", "Monetary outcome (thousands of euros)"))
    ax.set_ylabel(t("Valore percepito", "Perceived value"))
    ax.set_yticks([])
    ax.grid(visible=False)
    for lato in ("top", "right", "bottom", "left"):
        ax.spines[lato].set_visible(False)

    firma(fig, t("parametri sperimentali della teoria del prospetto",
                  "experimental parameters from prospect theory"), "—")
    return fig
