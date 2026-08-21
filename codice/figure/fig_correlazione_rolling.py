"""Cap. 11 — La correlazione non e' un numero: e' una serie storica.

Correlazione media a sessanta giorni, su due panieri: tre asset digitali, e gli
stessi tre piu' un indice azionario, un'azione industriale e un cambio. Il
valore non sta fermo in nessuno dei due, e in nessuno dei due resta uguale nei
periodi di calo profondo. Ma la distanza fra le due curve e' la terza regola
del capitolo, mostrata invece che enunciata: la diversificazione si compra
fuori dalla categoria, non aggiungendo la quindicesima cosa uguale.

Il paniere esteso si misura **solo nei giorni in cui la borsa di Milano e'
aperta** — le cripto non chiudono mai, e non c'e' altro modo di allineare i
due calendari. Non e' un dettaglio da nascondere: sulle stesse tre cripto,
misurate su quel calendario ridotto, la correlazione media passa da 0,675 a
0,678. La restrizione non sposta il risultato.
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
from cvbook.metriche import drawdown, rendimenti  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-11"
FINESTRA = 60
DA = dt.date(2020, 9, 1)

#: I due panieri del capitolo. Il primo e' quello storico del libro; il secondo
#: aggiunge due classi di attivita' che rispondono ad altri meccanismi.
NOMI = ["btcusdt", "ethusdt", "solusdt"]
ESTESO = ["btcusdt", "ethusdt", "solusdt", "ftsemib", "eni", "eurusd"]

#: I due pannelli hanno lo stesso asse verticale e lo stesso tratto: l'unica
#: differenza che l'occhio deve cogliere e' l'altezza della curva.
PANIERI = [
    (NOMI, t("tre asset digitali", "three digital assets")),
    (ESTESO, t("gli stessi tre più indice, azione e cambio",
               "the same three plus an index, a stock and an FX pair")),
]

DIDASCALIA = (
    "Correlazione media su finestre mobili di sessanta giorni, per due panieri. In "
    "alto, tre asset digitali: il valore oscilla fra 0,17 e 0,94 e nei periodi in cui "
    "il mercato è oltre il 30% sotto il massimo — le bande grigie — la media sale da "
    "0,68 a 0,79. In basso, gli stessi tre più l'indice della borsa italiana, "
    "un'azione industriale e il cambio euro-dollaro: la stessa misura scende a un "
    "terzo, e non arriva mai dove il paniere digitale passa quasi tutto il tempo. "
    "Anche qui sale nei periodi difficili, da 0,22 a 0,26 — quella parte non la "
    "aggira nessuno. Ma la distanza fra le due curve è quanto vale cercare la "
    "diversificazione fuori dalla categoria invece che dentro."
)


def _dati(nomi: list[str] | None = None):
    """Rendimenti allineati sulle date comuni a tutte le serie del paniere."""
    nomi = nomi or NOMI
    serie = [
        carica(n).filter(pl.col("data") >= DA)
        .select(["data", "chiusura"]).rename({"chiusura": n})
        for n in nomi
    ]
    base = serie[0]
    for s in serie[1:]:
        base = base.join(s, on="data")
    base = base.sort("data")
    M = np.column_stack([rendimenti(base[n].to_numpy()) for n in nomi])
    return base["data"].to_list()[1:], M


def _correlazione_mobile(M: np.ndarray) -> np.ndarray:
    coppie = np.triu_indices(M.shape[1], 1)
    return np.array([
        np.corrcoef(M[i - FINESTRA:i].T)[coppie].mean()
        for i in range(FINESTRA, len(M))
    ])


def misure(nomi: list[str]) -> dict:
    """Tutto ciò che il capitolo cita in prosa, calcolato una volta sola."""
    date, M = _dati(nomi)
    corr = _correlazione_mobile(M)
    date_c = date[FINESTRA:]
    dd = drawdown(np.concatenate([[1.0], np.cumprod(1 + M[:, 0])]))[FINESTRA + 1:]
    difficile = dd < -0.30
    return {
        "date": date_c, "corr": corr, "difficile": difficile,
        "media": float(corr.mean()),
        "min": float(corr.min()), "max": float(corr.max()),
        "media_difficile": float(corr[difficile].mean()),
        "media_tranquilla": float(corr[~difficile].mean()),
    }


def disegna(destinazione: str = "stampa"):
    from cvbook.layout import figsize

    fig, assi = plt.subplots(2, 1, figsize=figsize("alta"), sharex=True, sharey=True)

    numeri = {}
    for ax, (nomi, etichetta) in zip(assi, PANIERI):
        m = misure(nomi)
        numeri[etichetta] = {k: v for k, v in m.items()
                             if k not in ("date", "corr", "difficile")}

        ax.fill_between(m["date"], 0, 1, where=m["difficile"], color="#E0E0E0",
                        linewidth=0)
        ax.plot(m["date"], m["corr"], color="black", linestyle="-", linewidth=1.0)
        ax.axhline(m["media"], color="#595959", linestyle=":", linewidth=0.9)
        ax.annotate(t(f"media {num(m['media'], 2)}", f"mean {num(m['media'], 2)}"),
                    xy=(m["date"][40], m["media"]), xytext=(0, 7),
                    textcoords="offset points", fontsize=6.5,
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="white",
                              edgecolor="none"))
        ax.set_title(t(f"{len(nomi)} asset: {etichetta}", f"{len(nomi)} assets: {etichetta}"),
                     fontsize=7)
        ax.set_ylim(0, 1)

    assi[0].set_ylabel(t("Correlazione media a 60 giorni", "60-day average correlation"), fontsize=7)
    # La nota sta nel pannello in basso, che nella sua meta' superiore e' vuoto:
    # in quello in alto la curva passa dove finirebbe il testo.
    # The note sits in the bottom panel, whose upper half is empty: in the top
    # panel the curve runs right where the text would otherwise fall.
    assi[1].text(0.02, 0.94,
                 t("le bande grigie sono i periodi\noltre il 30% sotto il massimo",
                   "the grey bands are periods\nover 30% below the peak"),
                 transform=assi[1].transAxes, fontsize=6.5, linespacing=1.3, va="top")
    fig.autofmt_xdate(rotation=0, ha="center")

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte} e Yahoo Finance, chiusure giornaliere",
                  f"{fonte} and Yahoo Finance, daily closes"), estratto)

    disegna.numeri = numeri
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for etichetta, m in disegna.numeri.items():
        print(f"\n{etichetta}")
        print(f"  media {m['media']:.4f}  fra {m['min']:.3f} e {m['max']:.3f}")
        print(f"  nei cali profondi {m['media_difficile']:.4f}"
              f"  altrove {m['media_tranquilla']:.4f}")
