"""Cap. 8 — La stessa serie guardata in tre modi.

Il prezzo racconta una storia, i rendimenti ne raccontano un'altra, la
distribuzione una terza. Nessuna delle tre e' piu' vera delle altre: sono
tre domande diverse, e scegliere quale porre e' meta' del mestiere.
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
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-08"
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Gli stessi identici dati, tre rappresentazioni. Il prezzo mostra il "
    "percorso e invita a cercare figure e tendenze. I rendimenti giornalieri "
    "mostrano che quel percorso è fatto di scosse, e che le scosse si "
    "addensano in periodi. La distribuzione butta via il tempo e mostra solo "
    "quanto spesso succede cosa: perde l'ordine degli eventi e in cambio "
    "rende confrontabili asset ed epoche diverse. Chi guarda solo il primo "
    "pannello non sta guardando meno dati: sta facendo una domanda diversa, "
    "spesso senza saperlo."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt")
    date = df["data"].to_list()
    prezzi = df["chiusura"].to_numpy()
    r = rendimenti(prezzi)

    fig, assi = plt.subplots(3, 1, figsize=figsize("alta"))

    assi[0].plot(date, prezzi, color="black", linewidth=0.9)
    assi[0].set_yscale("log")
    assi[0].set_ylabel(t("Prezzo\n(log.)", "Price\n(log)"), fontsize=6.5)
    assi[0].set_yticks([1000, 10000, 100000])
    assi[0].set_yticklabels(["1k", "10k", "100k"], fontsize=6)
    assi[0].grid(which="minor", visible=False)

    assi[1].plot(date[1:], r * 100, color="black", linewidth=0.35)
    assi[1].axhline(0, color="#8C8C8C", linewidth=0.7)
    assi[1].set_ylabel(t("Variazione\ngiornaliera (%)", "Daily\nchange (%)"), fontsize=6.5)

    # I primi due pannelli guardano il tempo, il terzo guarda la distribuzione:
    # senza gli anni sui primi due la differenza non si vede.
    for a in (assi[0], assi[1]):
        a.xaxis.set_major_locator(mdates.YearLocator(2))
        a.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        a.tick_params(axis="x", labelsize=6)

    assi[2].hist(r * 100, bins=90, facecolor="white", edgecolor="black", linewidth=0.5)
    assi[2].set_xlabel(t("Variazione giornaliera (%)", "Daily change (%)"), fontsize=6.5)
    assi[2].set_ylabel(t("Numero\ndi giorni", "Number\nof days"), fontsize=6.5)
    assi[2].tick_params(labelsize=6)
    assi[2].set_xlim(-25, 25)

    for ax in assi[:2]:
        ax.tick_params(labelsize=6)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero 2017-2026", f"{fonte}, daily BTCUSDT 2017-2026"), estratto)
    return fig
