"""Cap. 4 — Cosa succede se scegli il meglio, dopo.

A sinistra: le cinque curve migliori estratte da mille generate a caso. Sono
quelle che finirebbero in vetrina. A destra: la distribuzione completa da cui
provengono, con la mediocrita' come norma e le due code entrambe rare.
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
from cvbook.simulazioni import equity_casuali, migliori_per_caso  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-04"
N_CURVE = 1000
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "A sinistra le cinque migliori curve di capitale fra mille generate dal "
    "puro caso: nessuna abilità dentro, eppure ognuna di esse, mostrata da "
    "sola, sembrerebbe la prova di un metodo. A destra la distribuzione "
    "completa dei mille risultati finali da cui sono state estratte: il "
    "grosso sta ammassato attorno al punto di partenza, e le due code sono "
    "entrambe sottili. È il motivo per cui un risultato eccezionale va "
    "guardato con più sospetto di uno pessimo, non con meno."
)


def disegna(destinazione: str = "stampa"):
    rng = np.random.default_rng(seed_for("migliori-per-caso"))
    curve = equity_casuali(N_CURVE, 500, volatilita_periodo=0.018, rng=rng)

    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"), width_ratios=[1.15, 1])

    migliori = migliori_per_caso(curve, 5)
    for k, curva in enumerate(migliori):
        sx.plot(curva * 100, linewidth=0.9, color=["#000000", "#404040", "#595959", "#737373", "#8C8C8C"][k])
    sx.axhline(100, color="black", linestyle=":", linewidth=0.75)
    sx.set_title(t("Le 5 migliori su 1.000", "The 5 best out of 1,000"), fontsize=8)
    sx.set_xlabel(t("Giorni", "Days"))
    sx.set_ylabel(t("Capitale (100 = iniziale)", "Capital (100 = starting)"))

    finali = curve[:, -1] * 100
    dx.hist(finali, bins=45, facecolor="white", edgecolor="black", linewidth=0.75, hatch="///")
    mediana = float(np.median(finali))
    # Le due righe distano nove unita' su un asse largo trecento: le etichette
    # non ci stanno una accanto all'altra alla stessa quota. Si apre una fascia
    # sopra l'istogramma e ci vanno tutte e due, su due livelli, ciascuna dalla
    # parte della propria riga. Prima «capitale» finiva sul picco delle barre.
    dx.set_ylim(0, dx.get_ylim()[1] * 1.28)
    alto = dx.get_ylim()[1]
    dx.axvline(100, color="black", linewidth=1.0, ymax=0.90)
    dx.axvline(mediana, color="#595959", linestyle="--", linewidth=0.9, ymax=0.78)
    dx.annotate(t("capitale iniziale", "starting capital"), xy=(100, alto * 0.90), xytext=(4, 0),
                textcoords="offset points", fontsize=6.5, ha="left", va="center")
    dx.annotate(t(f"mediana {num(mediana)}", f"median {num(mediana)}"), xy=(mediana, alto * 0.78),
                xytext=(-4, 0), textcoords="offset points", fontsize=6.5,
                ha="right", va="center", color="#404040")
    dx.set_title(t("Da dove vengono", "Where they come from"), fontsize=8)
    dx.set_xlabel(t("Capitale finale", "Final capital"))
    dx.set_ylabel(t("Numero di curve", "Number of curves"))
    dx.set_xlim(0, 320)

    firma(fig, t("simulazione, seme fisso, vantaggio atteso nullo",
                  "simulation, fixed seed, zero expected edge"), "—")
    return fig
