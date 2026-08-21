"""Cap. 5 — L'indice dei sopravvissuti contro l'indice di tutti.

Due panieri costruiti nello stesso giorno, con lo stesso peso su ogni asset.
Il primo contiene solo cio' che oggi e' ancora quotato; il secondo contiene
anche cio' che nel frattempo e' morto. La differenza fra le due curve non e'
una differenza di mercato: e' l'errore che si commette guardando indietro.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, mesi_italiani, num  # noqa: E402

CAPITOLO = "sec-cap-05"
INIZIO = dt.date(2021, 4, 1)
FINE = dt.date(2022, 12, 31)
SOPRAVVISSUTI = ["btcusdt", "ethusdt", "solusdt"]
MORTI = ["lunausdt", "fttusdt"]
DIDASCALIA = (
    "Due panieri a peso uguale costruiti il 1 aprile 2021. Quello chiaro contiene i "
    "tre asset che oggi sono ancora quotati; quello scuro contiene gli stessi tre più "
    "i due che nel frattempo sono morti — un token il cui prezzo è andato a zero in "
    "nove giorni e uno il cui mercato è stato chiuso. Chi guarda oggi solo cio' che "
    "esiste ancora misura il paniere chiaro e crede di aver misurato il mercato. La "
    "distanza fra le due curve è l'errore, e non è piccolo."
)


def _serie(nome: str) -> pl.DataFrame:
    return carica(nome).filter(
        (pl.col("data") >= INIZIO) & (pl.col("data") <= FINE)
    ).select(["data", "chiusura"]).rename({"chiusura": nome})


def _paniere(nomi: list[str]) -> tuple[list, np.ndarray]:
    base = _serie(nomi[0])
    for n in nomi[1:]:
        base = base.join(_serie(n), on="data", how="left")
    base = base.sort("data")
    date = base["data"].to_list()

    quote = []
    for n in nomi:
        colonna = base[n].to_numpy().astype(float)
        # Un asset delistato non "sparisce": resta al suo ultimo valore noto,
        # che e' quanto vale davvero per chi lo aveva in portafoglio.
        ultimo = colonna[0]
        riempita = np.empty_like(colonna)
        for k, v in enumerate(colonna):
            if not np.isnan(v):
                ultimo = v
            riempita[k] = ultimo
        quote.append(riempita / riempita[0])

    return date, np.mean(quote, axis=0) * 100


def disegna(destinazione: str = "stampa"):
    date, solo_vivi = _paniere(SOPRAVVISSUTI)
    _, tutti = _paniere(SOPRAVVISSUTI + MORTI)

    fig, ax = plt.subplots()
    ax.plot(date, solo_vivi, color="#8C8C8C", linestyle="--", linewidth=1.2)
    ax.plot(date, tutti, color="black", linestyle="-", linewidth=1.2)
    ax.axhline(100, color="black", linewidth=0.75, linestyle=":")

    # Legenda testuale in alto a sinistra: l'area e' libera e le etichette
    # agganciate all'ultimo punto si accavallano fra loro.
    ax.text(
        0.02, 0.97,
        t(f"solo i sopravvissuti — finisce a {num(solo_vivi[-1])}",
          f"survivors only — ends at {num(solo_vivi[-1])}"),
        transform=ax.transAxes, fontsize=7, color="#595959", va="top",
    )
    ax.text(
        0.02, 0.90,
        t(f"tutti, morti compresi — finisce a {num(tutti[-1])}",
          f"all, including the dead — ends at {num(tutti[-1])}"),
        transform=ax.transAxes, fontsize=7, color="black", va="top",
    )
    ax.plot([0.005, 0.015], [0.955, 0.955], transform=ax.transAxes,
            linestyle="--", color="#8C8C8C", linewidth=1.2, clip_on=False)
    ax.plot([0.005, 0.015], [0.885, 0.885], transform=ax.transAxes,
            linestyle="-", color="black", linewidth=1.2, clip_on=False)

    ax.set_ylabel(t("Valore del paniere (100 = 1 aprile 2021)", "Basket value (100 = April 1, 2021)"))
    ax.set_ylim(0, 640)
    mesi_italiani(ax, ogni_mesi=4)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, chiusure giornaliere di 5 mercati",
                  f"{fonte}, daily closes of 5 markets"), estratto)
    return fig
