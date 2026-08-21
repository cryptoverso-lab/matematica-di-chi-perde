"""Cap. 19 — Mille storie possibili invece dell'unica capitata.

La curva che hai ottenuto e' una realizzazione fra tante. Rimescolando i tuoi
stessi rendimenti a blocchi si ottengono i percorsi alternativi compatibili
con lo stesso processo: la loro dispersione e' cio' che il singolo risultato
non ti stava dicendo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook import seed_for  # noqa: E402
from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t as tr  # noqa: E402
from cvbook.metriche import drawdown_massimo, rendimenti  # noqa: E402
from cvbook.simulazioni import bootstrap_traiettorie  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-19"
N = 1000
DIDASCALIA = (
    "A sinistra: mille percorsi alternativi ottenuti rimescolando a blocchi di venti "
    "giorni gli stessi rendimenti realmente accaduti, con evidenziata la storia "
    "davvero capitata. A destra: la distribuzione del calo massimo di quei mille "
    "percorsi. La storia reale ha avuto un calo dell'83%, ma percorsi con la stessa "
    "identica materia prima arrivano ben oltre. Chi dimensiona la propria posizione "
    "sul peggio già visto sta dimensionando su un campione di uno."
)


def disegna(destinazione: str = "stampa"):
    r = rendimenti(carica("btcusdt")["chiusura"].to_numpy())
    rng = np.random.default_rng(seed_for("montecarlo-btc"))
    traiettorie = bootstrap_traiettorie(r, n_traiettorie=N, rng=rng, a_blocchi=20)
    reale = np.cumprod(1 + r)

    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"), width_ratios=[1.2, 1])

    x = np.arange(traiettorie.shape[1])
    for t in traiettorie[:180]:
        sx.plot(x, t, color="#C8C8C8", linewidth=0.35)
    sx.plot(x, np.median(traiettorie, axis=0), color="#595959", linestyle="--", linewidth=1.1)
    sx.plot(x, reale, color="black", linewidth=1.3)
    sx.set_yscale("log")
    sx.set_ylabel(tr("Capitale (× iniziale, log.)", "Capital (× starting, log scale)"))
    sx.set_xlabel(tr("Giorni", "Days"))
    sx.text(0.04, 0.95, tr("in nero: quello che è successo", "in black: what actually happened"),
            transform=sx.transAxes, fontsize=6.5, va="top")

    cali = np.array([drawdown_massimo(t) for t in traiettorie]) * 100
    dx.hist(cali, bins=40, facecolor="white", edgecolor="black", linewidth=0.7, hatch="///")
    reale_dd = drawdown_massimo(reale) * 100
    # La verticale si ferma poco sotto il bordo: portata fino in cima, su un
    # riquadro senza cornice superiore sembrava uscire dal grafico.
    dx.axvline(reale_dd, color="black", linewidth=1.3, ymax=0.94)

    # Le due etichette vanno agli angoli opposti, ciascuna dalla parte del
    # proprio valore: messe entrambe a destra, le due frecce si incrociavano
    # in mezzo all'istogramma e non si capiva quale puntasse a cosa. Sopra le
    # barre si apre una fascia libera alzando il limite dell'asse.
    peggiore = np.percentile(cali, 5)
    dx.set_ylim(0, dx.get_ylim()[1] * 1.30)
    alto = dx.get_ylim()[1]
    dx.annotate(tr(f"il 5% peggiore: {num(peggiore)}%", f"the worst 5%: {num(peggiore)}%"),
                xy=(peggiore, alto * 0.58), xytext=(0.02, 0.98),
                textcoords="axes fraction", fontsize=6.5, ha="left", va="top",
                arrowprops=dict(arrowstyle="->", linewidth=0.6, color="#595959"))
    dx.annotate(tr(f"la storia reale: {num(reale_dd)}%", f"the real history: {num(reale_dd)}%"),
                xy=(reale_dd, alto * 0.74), xytext=(0.98, 0.86),
                textcoords="axes fraction", fontsize=6.5, ha="right", va="top",
                arrowprops=dict(arrowstyle="->", linewidth=0.6, color="#595959"))

    dx.set_xlabel(tr("Calo massimo (%)", "Maximum drawdown (%)"))
    dx.set_ylabel(tr("Numero di percorsi", "Number of paths"))

    fonte, estratto = citazione("btcusdt")
    firma(fig, tr(f"{fonte}, ricampionamento a blocchi dei rendimenti reali",
                   f"{fonte}, block resampling of real returns"), estratto)
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto, salva

    for d in ("stampa", "schermo"):
        with contesto(d):
            salva(disegna(d), f"figure/{d}/montecarlo.png", d)
