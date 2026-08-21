"""Cap. 16 — Lo stesso identico test, con e senza un errore di una riga.

La versione sbagliata decide oggi usando il prezzo di chiusura di oggi, che
al momento della decisione non e' ancora noto. E' l'errore piu' comune di
tutti, produce curve spettacolari, e si vede solo se lo si cerca.
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
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-16"
FINESTRA = 20
DIDASCALIA = (
    "La stessa regola — restare investiti quando il prezzo è sopra la sua media a "
    "venti giorni — calcolata in due modi. Nella versione causale la media di oggi "
    "usa i prezzi fino a ieri e la decisione vale da domani. Nella versione con "
    "lookahead la media include la chiusura di oggi e la decisione si applica allo "
    "stesso giorno: un'informazione che al momento di decidere non esisteva. La "
    "differenza è una riga di codice, e produce una curva che sembra la scoperta "
    "di una vita."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt")
    date = df["data"].to_list()
    p = df["chiusura"].to_numpy()
    r = rendimenti(p)

    media = np.convolve(p, np.ones(FINESTRA) / FINESTRA, mode="full")[: len(p)]
    media[:FINESTRA] = np.nan

    # Causale: confronto fatto con dati fino a t, posizione applicata da t+1.
    segnale_causale = np.where(p[:-1] > media[:-1], 1.0, 0.0)
    # Con lookahead: la posizione di oggi usa il confronto di oggi.
    segnale_futuro = np.where(p[1:] > media[1:], 1.0, 0.0)

    valido = ~np.isnan(media[:-1])
    causale = np.cumprod(1 + np.where(valido, segnale_causale, 0) * r)
    futuro = np.cumprod(1 + np.where(valido, segnale_futuro, 0) * r)
    compra_tieni = np.cumprod(1 + r)

    fig, ax = plt.subplots()
    ax.plot(date[1:], futuro, color="black", linestyle="-", linewidth=1.3)
    ax.plot(date[1:], causale, color="#595959", linestyle="--", linewidth=1.2)
    ax.plot(date[1:], compra_tieni, color="#B0B0B0", linestyle=":", linewidth=1.1)
    ax.set_yscale("log")

    for y, testo, colore in [
        (0.95, t(f"con lookahead — {num(futuro[-1])}×", f"with lookahead — {num(futuro[-1])}×"), "black"),
        (0.88, t(f"causale — {num(causale[-1], 1)}×", f"causal — {num(causale[-1], 1)}×"), "#595959"),
        (0.81, t(f"compra e tieni — {num(compra_tieni[-1], 1)}×",
                  f"buy and hold — {num(compra_tieni[-1], 1)}×"), "#8C8C8C"),
    ]:
        ax.text(0.02, y, testo, transform=ax.transAxes, fontsize=7, color=colore, va="top")

    ax.set_ylabel(t("Capitale (× iniziale, scala log.)", "Capital (× starting, log scale)"))
    ax.grid(which="minor", visible=False)
    fig.autofmt_xdate(rotation=0, ha="center")

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero", f"{fonte}, daily BTCUSDT"), estratto)
    return fig
