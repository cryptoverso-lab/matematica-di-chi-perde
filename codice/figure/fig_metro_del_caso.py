"""Cap. 15 — Il metro: rispetto a cosa si giudica un risultato.

Una strategia semplice viene confrontata non con lo zero, ma con mille
strategie che entrano ed escono negli stessi giorni scelti a caso, con lo
stesso numero di operazioni e gli stessi costi. E' l'unico confronto che
risponde alla domanda giusta: sarebbe bastato il caso?
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook import seed_for  # noqa: E402
from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.regole import esegui, sopra_media  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-15"
FINESTRA = 50
COSTO = 0.0012
N_CASUALI = 1000
DIDASCALIA = (
    "Risultato di mille strategie che stanno dentro al mercato negli stessi giorni "
    "complessivi della strategia vera, ma scelti a caso, con lo stesso numero di "
    "entrate e uscite e gli stessi costi. La linea verticale è il risultato della "
    "strategia vera. La domanda a cui questa figura risponde non è \"ha guadagnato?\" "
    "ma \"ha fatto meglio del semplice essere stato dentro per altrettanto tempo?\". "
    "E' il confronto che quasi nessun backtest fa."
)


def disegna(destinazione: str = "stampa"):
    p = carica("btcusdt").sort("data")["chiusura"].to_numpy()

    # La regola e i costi vengono da `cvbook.regole`, cioe' dallo stesso motore
    # che usano il testo e i quaderni: se un numero cambia qui, cambia ovunque.
    segnale = sopra_media(p, FINESTRA)
    conto = esegui(p, segnale, costo=COSTO)

    def risultato(s: np.ndarray) -> float:
        return esegui(p, s, costo=COSTO)["finale"]

    vera = conto["finale"]
    giorni_dentro = int(segnale.sum())
    cambi = int(conto["operazioni"])

    # Il confronto deve essere equo: le strategie casuali devono avere lo stesso
    # numero di giorni dentro E lo stesso numero di operazioni, altrimenti pagano
    # costi diversi e il confronto e' truccato. Si costruiscono quindi come
    # blocchi contigui, non come giorni sparsi.
    n_blocchi = max(cambi // 2, 1)
    rng = np.random.default_rng(seed_for("metro-del-caso"))
    casuali = []
    for _ in range(N_CASUALI):
        s = np.zeros(len(p))
        # Ripartisce i giorni dentro in n_blocchi blocchi di lunghezza casuale,
        # collocati in posizioni casuali senza sovrapposizioni.
        tagli = np.sort(rng.choice(np.arange(1, giorni_dentro), size=n_blocchi - 1, replace=False)) \
            if n_blocchi > 1 else np.array([], dtype=int)
        lunghezze = np.diff(np.concatenate([[0], tagli, [giorni_dentro]]))
        posizioni = np.sort(rng.choice(len(s) - int(lunghezze.max()), size=n_blocchi, replace=False))
        for inizio, lung in zip(posizioni, lunghezze):
            s[inizio:inizio + lung] = 1.0
        casuali.append(risultato(s))
    casuali = np.array(casuali)

    fig, ax = plt.subplots()
    ax.hist(casuali, bins=45, facecolor="white", edgecolor="black", linewidth=0.7, hatch="///")
    # Si ferma poco sotto il bordo: il riquadro non ha cornice superiore, e
    # una verticale che arriva in cima sembra uscire dal grafico.
    ax.axvline(vera, color="black", linewidth=1.6, ymax=0.94)

    percentile = (casuali < vera).mean() * 100
    ax.annotate(
        t(f"la strategia vera: {num(vera, 1)}×\nmeglio del {num(percentile)}% dei casi",
          f"the real strategy: {num(vera, 1)}×\nbetter than {num(percentile)}% of the cases"),
        xy=(vera, 0),
        xytext=(8, 70),
        textcoords="offset points",
        fontsize=7,
        linespacing=1.35,
        arrowprops=dict(arrowstyle="->", linewidth=0.75, color="black"),
    )
    ax.text(0.02, 0.96,
            t(f"{N_CASUALI} strategie casuali · {giorni_dentro} giorni dentro · {cambi} operazioni",
              f"{N_CASUALI} random strategies · {giorni_dentro} days in market · {cambi} trades"),
            transform=ax.transAxes, fontsize=6.5, va="top")

    ax.set_xlabel(t("Capitale finale (× iniziale)", "Final capital (× starting)"))
    ax.set_ylabel(t("Numero di strategie casuali", "Number of random strategies"))
    ax.set_xscale("log")
    ax.set_xticks([0.1, 1, 10, 100])
    ax.set_xticklabels(["0,1×", "1×", "10×", "100×"])
    ax.set_ylim(0, 620)
    ax.grid(which="minor", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT — costi dello 0,12% per giro",
                  f"{fonte}, BTCUSDT — 0.12% cost per round trip"), estratto)

    disegna.numeri = {
        "vera": vera,
        "giorni_dentro": giorni_dentro,
        "operazioni": cambi,
        "mediana_casuali": float(np.median(casuali)),
        "percentile": float(percentile),
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:18s} {v}")
