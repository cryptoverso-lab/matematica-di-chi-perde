"""Cap. 6 — Quanto costa vendere i vincenti e tenere i perdenti.

Simulazione su prezzi veri: due comportamenti applicati alla stessa serie e
allo stesso capitale. Il primo mantiene la posizione; il secondo fa quello che
fa quasi tutti — chiude quando e' in utile di poco, resta quando e' in perdita.
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

CAPITOLO = "sec-cap-06"
SOGLIA_UTILE = 0.10    # chiude quando il guadagno raggiunge il 10%
SOGLIA_PERDITA = 0.50  # resta finche' la perdita non raggiunge il 50%
COSTO = 0.0012
DIDASCALIA = (
    "Due comportamenti sulla stessa serie di prezzi e sullo stesso capitale, "
    "Bitcoin 2017-2026, costi dello 0,12% per giro inclusi in entrambi. Il primo "
    "compra e non tocca più nulla. Il secondo fa cio' che l'esperienza dei conti "
    "reali documenta: chiude appena è in utile del 10%, e resta dentro finché la "
    "perdita non raggiunge il 50%, poi rientra. Nessuna previsione distingue i due: "
    "solo la soglia a cui scatta la decisione di chiudere."
)


def _simula_disposition(prezzi: np.ndarray) -> np.ndarray:
    capitale = np.empty(len(prezzi))
    capitale[0] = 1.0
    ingresso = prezzi[0]
    quota = 1.0 / prezzi[0]
    liquido = 0.0
    dentro = True

    for i in range(1, len(prezzi)):
        if dentro:
            valore = quota * prezzi[i]
            variazione = prezzi[i] / ingresso - 1.0
            if variazione >= SOGLIA_UTILE or variazione <= -SOGLIA_PERDITA:
                liquido = valore * (1 - COSTO)
                dentro = False
                valore = liquido
            capitale[i] = valore
        else:
            # Rientra il giorno successivo: e' cio' che accade nella pratica,
            # la liquidita' non resta ferma a lungo.
            ingresso = prezzi[i]
            quota = liquido * (1 - COSTO) / prezzi[i]
            dentro = True
            capitale[i] = quota * prezzi[i]

    return capitale


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt")
    prezzi = df["chiusura"].to_numpy()
    date = df["data"].to_list()

    tieni = np.concatenate([[1.0], np.cumprod(1 + rendimenti(prezzi))]) * (1 - COSTO)
    disp = _simula_disposition(prezzi)

    fig, ax = plt.subplots()
    ax.plot(date, tieni, color="black", linestyle="-", linewidth=1.2)
    ax.plot(date, disp, color="#8C8C8C", linestyle="--", linewidth=1.2)
    ax.set_yscale("log")

    ax.text(0.02, 0.96, t(f"non tocca nulla — finisce a {num(tieni[-1], 1)}×",
                          f"never touches it — ends at {num(tieni[-1], 1)}×"),
            transform=ax.transAxes, fontsize=7, va="top")
    ax.text(0.02, 0.89, t(f"prende il piccolo utile — finisce a {num(disp[-1], 1)}×",
                          f"takes the small profit — ends at {num(disp[-1], 1)}×"),
            transform=ax.transAxes, fontsize=7, color="#595959", va="top")

    ax.set_ylabel(t("Capitale (× iniziale, scala log.)", "Capital (× starting, log scale)"))
    ax.set_yticks([0.5, 1, 5, 20])
    ax.set_yticklabels(["0,5×", "1×", "5×", "20×"])
    ax.grid(which="minor", visible=False)
    fig.autofmt_xdate(rotation=0, ha="center")

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, simulazione su BTCUSDT giornaliero",
                  f"{fonte}, simulation on daily BTCUSDT"), estratto)
    return fig
