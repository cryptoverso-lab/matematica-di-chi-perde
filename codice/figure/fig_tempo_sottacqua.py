"""Cap. 10 — Il rischio misurato in tempo, non in percentuale.

La volatilita' e' un numero che si dimentica. Il tempo passato sotto il proprio
massimo precedente e' l'esperienza che si vive davvero, ed e' molto piu' lunga
di quanto chiunque immagini.

I due pannelli in alto mostrano la stessa misura su due mercati che non hanno
niente in comune: nove anni di Bitcoin e ventisei di una blue chip industriale
quotata a Milano. Il pannello in basso li confronta soglia per soglia. Cambia
la profondita', non il fatto: si sta sotto il proprio massimo quasi sempre,
anche comprando la piu' noiosa delle azioni.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import drawdown, rendimenti  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-10"
SOGLIE = np.array([5, 10, 20, 30, 50, 70])
MERCATI = [("btcusdt", "Bitcoin, 2017-2026"), ("eni", "ENI, 2000-2026")]
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Sopra: distanza dal massimo precedente, giorno per giorno, su Bitcoin e "
    "su un'azione industriale quotata a Milano. La zona nera è il tempo "
    "passato sotto il proprio picco — che in entrambi i casi è quasi tutto il "
    "tempo. Sotto: per quanta parte del periodo il capitale è rimasto oltre "
    "una certa distanza dal massimo. Sul titolo le quote sono 28% oltre −20% "
    "e 0,7% oltre −50%; su Bitcoin, che oscilla il doppio, 71% e 40%. La "
    "profondità cambia, la condizione no: il 73% del tempo sotto il 5% dal "
    "massimo per il titolo, l'89% per Bitcoin."
)


def sottacqua(nome: str) -> dict:
    df = carica(nome).sort("data")
    curva = np.concatenate([[1.0], np.cumprod(1 + rendimenti(df["chiusura"].to_numpy()))])
    dd = drawdown(curva)
    return {
        "date": df["data"].to_list(),
        "dd": dd * 100,
        "quote": {int(s): float((dd < -s / 100).mean() * 100) for s in SOGLIE},
        "peggiore": float(dd.min() * 100),
    }


def disegna(destinazione: str = "stampa"):
    dati = {nome: sottacqua(nome) for nome, _ in MERCATI}

    fig = plt.figure(figsize=figsize("alta"))
    griglia = fig.add_gridspec(2, 2, height_ratios=[1.15, 1])
    alto = [fig.add_subplot(griglia[0, 0]), fig.add_subplot(griglia[0, 1])]
    basso = fig.add_subplot(griglia[1, :])

    for ax, (nome, titolo) in zip(alto, MERCATI):
        d = dati[nome]
        ax.fill_between(d["date"], d["dd"], 0, color="#404040", linewidth=0)
        ax.set_title(titolo, fontsize=7)
        ax.set_ylim(-90, 3)
        ax.xaxis.set_major_locator(mdates.YearLocator(3 if nome == "btcusdt" else 8))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=6.5)
    alto[0].set_ylabel(t("Distanza dal massimo (%)", "Distance from peak (%)"), fontsize=7)
    alto[1].tick_params(axis="y", labelleft=False)

    x = np.arange(len(SOGLIE))
    larghezza = 0.36
    stili = [("#404040", ""), ("white", "///")]
    for j, ((nome, titolo), (colore, retino)) in enumerate(zip(MERCATI, stili)):
        quote = [dati[nome]["quote"][int(s)] for s in SOGLIE]
        barre = basso.bar(x + (j - 0.5) * larghezza, quote, width=larghezza,
                          facecolor=colore, edgecolor="black", linewidth=0.75,
                          hatch=retino, label=titolo.split(",")[0])
        for barra, q in zip(barre, quote):
            basso.annotate(num(q, 0) if q >= 1 else num(q, 1),
                           xy=(barra.get_x() + barra.get_width() / 2, q),
                           xytext=(0, 2), textcoords="offset points",
                           ha="center", fontsize=6.0)

    basso.set_xticks(x)
    basso.set_xticklabels([f"−{s}%" for s in SOGLIE])
    basso.set_ylabel(t("% del tempo\noltre quella soglia", "% of time\nbeyond that threshold"), fontsize=7)
    basso.set_ylim(0, 108)
    basso.grid(axis="x", visible=False)
    basso.legend(loc="upper right", fontsize=6.5, ncols=2)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte} (BTCUSDT) e Yahoo Finance (ENI.MI), chiusure giornaliere",
                  f"{fonte} (BTCUSDT) and Yahoo Finance (ENI.MI), daily closes"),
          estratto)

    disegna.numeri = {
        nome: {"quote": d["quote"], "peggiore": d["peggiore"]}
        for nome, d in dati.items()
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for nome, d in disegna.numeri.items():
        quote = ", ".join(f"−{s}%: {q:.1f}%" for s, q in d["quote"].items())
        print(f"{nome}: peggior calo {d['peggiore']:.1f}%  ·  {quote}")
