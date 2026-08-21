"""Cap. 14 — Quante operazioni servono per distinguere l'abilita' dal caso.

Non e' una domanda retorica: ha una risposta numerica, e la risposta e' quasi
sempre molto piu' grande del numero di operazioni che chiunque abbia fatto.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.simulazioni import quanti_servono  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-14"
VANTAGGI = np.array([0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01])
DIDASCALIA = (
    "Numero di operazioni necessarie per stabilire, con i criteri statistici usuali, "
    "che un vantaggio esiste davvero e non è rumore. Sull'asse orizzontale il "
    "vantaggio medio per operazione; sull'asse verticale quante operazioni servono, "
    "in scala logaritmica. Le due curve corrispondono a due livelli di oscillazione "
    "dei risultati. Con un vantaggio dello 0,1% per operazione e la volatilità "
    "osservata su Bitcoin servono circa ottomila operazioni: a una al giorno di "
    "mercato, trentun anni. Le linee tratteggiate mostrano quante operazioni ha realmente "
    "fatto chi dice di aver verificato il proprio metodo."
)


def disegna(destinazione: str = "stampa"):
    sigma_alta = float(rendimenti(carica("btcusdt")["chiusura"].to_numpy()).std(ddof=1))
    sigma_bassa = sigma_alta / 3

    fig, ax = plt.subplots()

    for sigma, etichetta, tratto, grigio in [
        (sigma_alta, t(f"oscillazione {num(sigma_alta * 100, 1)}% per operazione",
                        f"swing {num(sigma_alta * 100, 1)}% per trade"), "-", "#000000"),
        (sigma_bassa, t(f"oscillazione {num(sigma_bassa * 100, 1)}% per operazione",
                         f"swing {num(sigma_bassa * 100, 1)}% per trade"), "--", "#8C8C8C"),
    ]:
        n = [quanti_servono(v, sigma) for v in VANTAGGI]
        # Le due curve corrono parallele e vicine: un'etichetta sul tracciato
        # cancella un pezzo di linea, quindi si usa la legenda.
        ax.plot(VANTAGGI * 100, n, linestyle=tratto, color=grigio, linewidth=1.3,
                marker="o", markersize=3, label=etichetta)

    # Le etichette delle due soglie stanno all'estremita' sinistra: le curve
    # scendono da sinistra a destra e proprio a destra passano all'altezza
    # delle due righe tratteggiate, che e' dove il testo finiva sotto il tratto.
    for quante, testo in [
        (40, t("40 operazioni", "40 trades")),
        (250, t("un anno di operatività quotidiana", "a year of daily trading")),
    ]:
        ax.axhline(quante, color="#595959", linestyle=":", linewidth=0.8)
        ax.annotate(testo, xy=(0.021, quante), xytext=(0, 3),
                    textcoords="offset points", fontsize=6.5, ha="left")

    ax.legend(loc="upper right", fontsize=6.5)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(t("Vantaggio medio per operazione (%)", "Average edge per trade (%)"))
    ax.set_ylabel(t("Operazioni necessarie (scala log.)", "Trades required (log scale)"))
    ax.set_xticks([0.02, 0.1, 0.5, 1])
    ax.set_xticklabels(["0,02%", "0,1%", "0,5%", "1%"])
    ax.set_yticks([10, 1000, 100_000, 10_000_000])
    ax.set_yticklabels(["10", "1.000", "100.000", t("10 milioni", "10 million")])
    ax.grid(which="minor", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"calcolo di potenza statistica · volatilità da {fonte}",
                  f"statistical power calculation · volatility from {fonte}"), estratto)
    return fig
