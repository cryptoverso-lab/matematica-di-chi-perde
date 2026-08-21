"""Cap. 1 — La dispersione degli esiti a un anno, in funzione del solo giorno d'ingresso.

Stesso asset, stessa strategia (comprare e tenere dodici mesi), nessuna abilita'
richiesta: cambia soltanto il giorno in cui si e' cominciato.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-01"
ORIZZONTE = 365
DIDASCALIA = (
    "Esito dopo dodici mesi per ciascuno dei 2.875 giorni in cui si sarebbe potuto "
    "cominciare, comprando Bitcoin e tenendolo fermo. La stessa identica strategia "
    "produce risultati che vanno da −83% a +1.092%: la barra più alta non è vicina "
    "alla media, e un terzo dei giorni d'ingresso finisce in perdita. Chi ha guadagnato "
    "e chi ha perso hanno fatto esattamente la stessa cosa."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt")
    p = df["chiusura"].to_numpy()
    esiti = (p[ORIZZONTE:] / p[:-ORIZZONTE] - 1.0) * 100

    fig, ax = plt.subplots()

    bordi = np.arange(-100, 1150, 25)
    in_perdita = esiti[esiti < 0]
    in_utile = esiti[esiti >= 0]

    ax.hist(in_perdita, bins=bordi, color="#404040", edgecolor="black", linewidth=0.75)
    ax.hist(
        in_utile,
        bins=bordi,
        facecolor="white",
        edgecolor="black",
        linewidth=0.75,
        hatch="///",
    )

    # La riga dello zero si ferma all'altezza delle barre: portata fino in
    # cima lasciava un trattino sospeso nel vuoto che sembrava un difetto.
    ax.axvline(0, color="black", linewidth=1.0, ymax=0.84)

    quota = (esiti < 0).mean() * 100
    ax.annotate(
        t(f"{quota:.0f}% degli ingressi\nfinisce in perdita",
          f"{quota:.0f}% of entries\nend in a loss"),
        xy=(-100, 425),
        fontsize=7,
        ha="left",
        va="top",
        linespacing=1.3,
        bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none"),
    )
    # L'asse si ferma a +700% perche' oltre le barre sono invisibili; la coda
    # tagliata va dichiarata, con quante osservazioni contiene e quanto vale
    # la migliore. Prima l'etichetta annunciava un massimo che il grafico non
    # mostrava, sospesa in mezzo al bianco senza nulla a cui riferirsi.
    ax.set_xlim(-105, 705)
    oltre = int((esiti > 700).sum())
    ax.annotate(
        t(
            f"oltre il bordo destro: {oltre} ingressi\n"
            f"sopra il +700%, il migliore\n"
            f"a {num(esiti.max(), segno=True)}%",
            f"beyond the right edge: {oltre} entries\n"
            f"above +700%, the best\n"
            f"at {num(esiti.max(), segno=True)}%",
        ),
        xy=(0.985, 0.60),
        xycoords="axes fraction",
        fontsize=6.5,
        ha="right",
        va="top",
        linespacing=1.35,
        color="#404040",
    )
    ax.annotate(
        t(f"mediana {num(np.median(esiti), segno=True)}%",
          f"median {num(np.median(esiti), segno=True)}%"),
        xy=(np.median(esiti), 265),
        xytext=(180, 330),
        textcoords="data",
        fontsize=7,
        ha="left",
        arrowprops=dict(arrowstyle="->", linewidth=0.75, color="black"),
    )

    ax.set_xlabel(t("Risultato dopo dodici mesi (%)", "Outcome after twelve months (%)"))
    ax.set_ylabel(t("Numero di giorni d'ingresso", "Number of entry days"))
    ax.set_xlim(-110, 700)
    ax.set_ylim(0, 430)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero 2017-2026",
                  f"{fonte}, daily BTCUSDT 2017-2026"), estratto)
    return fig
