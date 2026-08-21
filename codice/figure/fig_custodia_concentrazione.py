"""Cap. custodia — Dieci anni di mercato vero, con e senza il rischio di sede.

I rendimenti sono quelli realmente accaduti, ricampionati a blocchi per non
distruggere i grappoli di volatilita'. L'unica cosa aggiunta e' un evento raro:
ogni anno, con probabilita' del 2%, la sede in cui sta una quota del capitale
smette di restituirlo. Il rendimento medio del mercato non cambia. Cambia la
distribuzione di cio' che rimane in mano.
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
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.simulazioni import bootstrap_traiettorie  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-custodia"
ANNI = 10
GIORNI = 365 * ANNI
N_PERCORSI = 5000
RISCHIO_ANNUO = 0.02
QUOTE = [1.00, 0.50, 0.20]

#: Si disegnano due curve su tre. La terza — metà del capitale in una sede —
#: si calcola e finisce nei numeri del capitolo, ma **non si traccia**: sta a
#: tre decimi di decade da quella del 20%, e su otto decadi di asse
#: logaritmico le due sono indistinguibili a occhio. Tre curve di cui due
#: sovrapposte sono una legenda che promette piu' di quanto la figura mostri.
QUOTE_DISEGNATE = [1.00, 0.20]

DIDASCALIA = (
    "Capitale dopo dieci anni su cinquemila percorsi ricampionati dai rendimenti "
    "realmente accaduti, con un evento di custodia che ogni anno ha il 2% di "
    "probabilità di azzerare la quota depositata. Le due curve differiscono solo per "
    "quanta parte del capitale sta in una sede sola. La mediana si sposta poco — da "
    "8,7 a 14,2 volte il capitale — mentre è la coda sinistra a cambiare del tutto: "
    "con tutto in un posto il 26% dei percorsi finisce sotto il capitale iniziale e "
    "il 5% peggiore va sostanzialmente a zero; con un quinto sono l'11% e 0,47 "
    "volte. Tenere tutto in un posto solo non riduce il rendimento medio: aumenta "
    "la probabilità di non arrivare in fondo."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt").sort("data")
    r = rendimenti(df["chiusura"].to_numpy())

    rng = np.random.default_rng(seed_for("custodia"))
    percorsi = bootstrap_traiettorie(r[:GIORNI] if len(r) > GIORNI else r,
                                     n_traiettorie=N_PERCORSI, rng=rng, a_blocchi=20)
    finali_mercato = percorsi[:, -1]

    # Un sorteggio annuo indipendente per ogni percorso e per ogni anno.
    colpito = rng.random((N_PERCORSI, ANNI)) < RISCHIO_ANNUO
    almeno_uno = colpito.any(axis=1)

    fig, ax = plt.subplots()

    stili = {1.00: ("-", "#000000"), 0.50: ("--", "#595959"), 0.20: ("-.", "#595959")}
    numeri = {}
    for quota in QUOTE:
        finali = np.where(almeno_uno, finali_mercato * (1 - quota), finali_mercato)
        finali = np.maximum(finali, 1e-4)
        ordinati = np.sort(finali)
        probabilita = np.arange(1, len(ordinati) + 1) / len(ordinati) * 100
        if quota in QUOTE_DISEGNATE:
            # Le curve si toccano nella parte alta: etichettarle sul tracciato
            # le sovrapporrebbe. La legenda sta nell'angolo vuoto.
            tratto, grigio = stili[quota]
            ax.plot(ordinati, probabilita, linestyle=tratto, color=grigio,
                    linewidth=1.2,
                    label=t(f"{quota:.0%} del capitale in una sede",
                             f"{quota:.0%} of capital in one venue"))
        numeri[f"quota {quota:.0%}"] = {
            "mediana": float(np.median(finali)),
            "sotto_capitale": float((finali < 1).mean()),
            "peggiore_5pct": float(np.percentile(finali, 5)),
        }

    ax.axvline(1.0, color="#BFBFBF", linewidth=0.9)
    ax.annotate(t("capitale iniziale", "starting capital"), xy=(1.0, 96), xytext=(3, 0),
                textcoords="offset points", fontsize=6.5)

    # Il numero che il capitolo usa — la quota di percorsi che finisce sotto il
    # capitale iniziale — si scrive accanto alla verticale, uno per curva:
    # leggerlo sul tracciato, dove le due curve si avvicinano, e' scomodo.
    for quota in QUOTE_DISEGNATE:
        y = numeri[f"quota {quota:.0%}"]["sotto_capitale"] * 100
        ax.annotate(f"{y:.0f}%", xy=(1.0, y), xytext=(-4, 0),
                    textcoords="offset points", fontsize=6.5, ha="right",
                    va="center",
                    bbox=dict(boxstyle="square,pad=0.12", facecolor="white",
                              edgecolor="none"))
    ax.set_xscale("log")
    ax.set_xlabel(t("Capitale dopo dieci anni (volte quello iniziale, scala log)",
                     "Capital after ten years (× starting capital, log scale)"))
    ax.set_ylabel(t("Percorsi con esito peggiore o uguale (%)", "Paths with equal or worse outcome (%)"))
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", fontsize=6.5)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, ricampionamento a blocchi di 20 giorni",
                  f"{fonte}, 20-day block resampling"), estratto)

    disegna.numeri = numeri | {
        "prob_almeno_un_evento": float(almeno_uno.mean()),
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} {v}")
