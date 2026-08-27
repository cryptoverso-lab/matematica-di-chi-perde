"""Cap. regimi — I periodi agitati durano, non lampeggiano.

Due misure della stessa cosa. A sinistra: sapendo che oggi il mercato e' nel
suo quarto piu' agitato, quanto e' probabile che lo sia ancora fra un mese?
Le due finestre di trenta giorni non si sovrappongono, quindi il legame non e'
un artefatto del modo in cui e' calcolata la misura. A destra: la durata dei
periodi agitati, contro quella che avrebbero se i giorni fossero indipendenti.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import GIORNI_ANNO, rendimenti  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-regimi"
FINESTRA = 30
ORIZZONTE = 30
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "A sinistra: probabilità che il mercato sia agitato fra trenta giorni — "
    "volatilità nel quarto più alto — a seconda di com'è oggi. Senza memoria "
    "le tre barre sarebbero uguali al 25%. Le due finestre di misura non si "
    "sovrappongono: il legame non è un effetto del calcolo. A destra: quanto "
    "durano i periodi agitati, nella storia vera e in una storia con gli "
    "stessi giorni agitati sparsi a caso. Pochi episodi lunghi contro "
    "moltissimi episodi da un giorno — 32 contro 631, il più lungo 187 giorni "
    "contro 7. Il rischio non arriva sparso: arriva a stagioni."
)


def _regime():
    df = carica("btcusdt").sort("data")
    r = rendimenti(df["chiusura"].to_numpy())
    vol = np.array([
        np.std(r[i - FINESTRA:i], ddof=1) * np.sqrt(GIORNI_ANNO)
        for i in range(FINESTRA, len(r) + 1)
    ])
    return vol, vol > np.percentile(vol, 75)


def _sequenze(maschera: np.ndarray) -> np.ndarray:
    """Lunghezza di ogni tratto consecutivo di `True`."""
    lunghezze, corrente = [], 0
    for x in maschera:
        if x:
            corrente += 1
        elif corrente:
            lunghezze.append(corrente)
            corrente = 0
    if corrente:
        lunghezze.append(corrente)
    return np.array(lunghezze)


def disegna(destinazione: str = "stampa"):
    vol, alto = _regime()

    oggi, dopo = alto[:-ORIZZONTE], alto[ORIZZONTE:]
    base = float(alto.mean())
    da_alto = float(dopo[oggi].mean())
    da_calmo = float(dopo[~oggi].mean())

    seq = _sequenze(alto)
    rng = np.random.default_rng(0)
    seq_finto = _sequenze(rng.random(len(alto)) < base)

    fig, (sx, dx) = plt.subplots(1, 2, figsize=(4.25, 4.25 * 0.62))

    valori = [da_calmo * 100, base * 100, da_alto * 100]
    barre = sx.bar(
        [t("oggi\ncalmo", "today\ncalm"), t("senza\nmemoria", "no\nmemory"),
         t("oggi\nagitato", "today\nturbulent")],
        valori, facecolor="white", edgecolor="black", linewidth=0.75,
        hatch="///", width=0.6)
    barre[1].set_hatch("")
    barre[1].set_facecolor("#D9D9D9")
    barre[2].set_hatch("")
    barre[2].set_facecolor("#404040")
    for k, v in enumerate(valori):
        sx.annotate(f"{v:.0f}%", xy=(k, v), xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=7)
    sx.set_ylabel(t("Agitato fra 30 giorni (%)", "Turbulent in 30 days (%)"))
    sx.set_ylim(0, max(valori) * 1.3)
    sx.grid(axis="x", visible=False)

    bordi = np.logspace(0, np.log10(max(seq.max(), seq_finto.max()) + 1), 14)
    dx.hist(seq, bins=bordi, facecolor="#404040", edgecolor="black", linewidth=0.75)
    dx.hist(seq_finto, bins=bordi, histtype="step", edgecolor="black",
            linewidth=0.9, linestyle="--")
    dx.set_xscale("log")
    dx.set_yscale("log")
    dx.set_xlabel(t("Durata del periodo agitato (giorni)", "Duration of the turbulent period (days)"))
    dx.set_ylabel(t("Quante volte", "How many times"))
    # Due righe, non tre: spezzare «giorni indipendenti» faceva finire una
    # riga di una parola sola, allineata a destra, che sembrava un rientro.
    dx.text(0.97, 0.96, t("pieno: mercato vero\ntratteggio: giorni indipendenti",
                          "solid: real market\ndashed: independent days"),
            transform=dx.transAxes, fontsize=6.5, ha="right", va="top", linespacing=1.35)
    dx.grid(axis="x", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, chiusure giornaliere", f"{fonte}, daily closes"), estratto)

    disegna.numeri = {
        "base": base,
        "da_alto": da_alto,
        "da_calmo": da_calmo,
        "rapporto": da_alto / da_calmo,
        "episodi_veri": len(seq),
        "mediana_vera": float(np.median(seq)),
        "max_vero": int(seq.max()),
        "episodi_finti": len(seq_finto),
        "mediana_finta": float(np.median(seq_finto)),
        "max_finto": int(seq_finto.max()),
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:18s} {v}")
