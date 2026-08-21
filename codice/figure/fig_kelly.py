"""Cap. 20 — Quanto rischiare: la curva che sale, tocca la vetta e crolla.

Con un vantaggio reale esiste una frazione del capitale che massimizza la
crescita di lungo periodo. Sopra quella frazione la crescita non aumenta:
diminuisce, e oltre una certa soglia diventa distruzione garantita.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook import seed_for  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-20"
P_VINCITA = 0.55
RAPPORTO = 1.0
OPERAZIONI = 500
CAMPIONI = 3000
DIDASCALIA = (
    "Simulazione di un gioco con un vantaggio reale: si vince il 55% delle volte, "
    "guadagnando quanto si rischia. A sinistra, capitale mediano dopo 500 operazioni "
    "al variare della frazione di capitale rischiata ogni volta. La crescita è "
    "massima attorno al 10%: rischiare di più non aumenta il risultato, lo riduce, "
    "e oltre il 30% lo distrugge — pur avendo il vantaggio. A destra, la probabilità "
    "di ritrovarsi con meno di un quinto del capitale iniziale. Avere ragione non "
    "basta: bisogna anche rischiare la quantita' giusta."
)


def disegna(destinazione: str = "stampa"):
    rng = np.random.default_rng(seed_for("kelly"))
    esiti = rng.random((CAMPIONI, OPERAZIONI)) < P_VINCITA
    frazioni = np.arange(0.01, 0.61, 0.01)

    mediane, rovine = [], []
    for f in frazioni:
        passi = np.where(esiti, 1 + f * RAPPORTO, 1 - f)
        curve = np.cumprod(passi, axis=1)
        mediane.append(np.median(curve[:, -1]))
        rovine.append((curve[:, -1] < 0.2).mean() * 100)

    kelly = P_VINCITA - (1 - P_VINCITA) / RAPPORTO

    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"))

    sx.plot(frazioni * 100, mediane, color="black", linewidth=1.3)
    sx.axhline(1.0, color="#8C8C8C", linestyle=":", linewidth=0.9)
    sx.axvline(kelly * 100, color="#595959", linestyle="--", linewidth=0.9)
    sx.annotate(t(f"massimo teorico a {kelly * 100:.0f}%", f"theoretical maximum at {kelly * 100:.0f}%"),
                xy=(kelly * 100, max(mediane)),
                xytext=(0.97, 0.93), textcoords="axes fraction", fontsize=6.5,
                ha="right", va="center",
                arrowprops=dict(arrowstyle="->", linewidth=0.6, color="#595959"))
    sx.set_yscale("log")
    # Oltre un certo punto la mediana crolla di trenta ordini di grandezza: se
    # si lascia l'asse libero, tutta la parte leggibile si schiaccia in cima.
    # Si taglia a 1e-9 e si dice che sotto la curva esce dal grafico.
    sx.set_ylim(1e-9, max(mediane) * 3)
    # «sotto questo punto» non indicava nessun punto: adesso l'etichetta dice
    # a quale frazione la curva esce, e quel numero lo calcola il codice.
    esce = frazioni[np.argmax(np.array(mediane) < 1e-9)] * 100
    sx.text(0.98, 0.02,
            t(f"oltre il {esce:.0f}% esce dal grafico", f"beyond {esce:.0f}% it falls off the chart"),
            transform=sx.transAxes, fontsize=6, ha="right", va="bottom",
            color="#595959",
            bbox=dict(boxstyle="square,pad=0.15", facecolor="white",
                      edgecolor="none"))
    sx.set_xlabel(t("Frazione di capitale rischiata (%)", "Fraction of capital risked (%)"))
    sx.set_ylabel(t("Capitale mediano dopo 500 operazioni", "Median capital after 500 trades"))

    dx.plot(frazioni * 100, rovine, color="black", linewidth=1.3)
    dx.axvline(kelly * 100, color="#595959", linestyle="--", linewidth=0.9)
    dx.set_xlabel(t("Frazione di capitale rischiata (%)", "Fraction of capital risked (%)"))
    dx.set_ylabel(t("Probabilità di perdere l'80% (%)", "Probability of losing 80% (%)"))
    dx.set_ylim(0, 100)

    firma(fig, t("simulazione con vantaggio reale del 5%, seme fisso",
                  "simulation with a real 5% edge, fixed seed"), "—")
    return fig
