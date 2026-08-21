"""Cap. analisi tecnica — Sei regole da manuale, misurate tutte insieme.

Nessuna selezione: si prendono le sei regole che qualunque manuale presenta
come fondamentali, si applicano allo stesso mercato, sullo stesso periodo, con
gli stessi costi, e si mostrano tutti e sei i risultati. Compresi quelli
imbarazzanti.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import drawdown_massimo  # noqa: E402
from cvbook.regole import CATALOGO, compra_e_tieni, esegui  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-tecnica"
COSTO = 0.0012
DIDASCALIA = (
    "Sei regole tecniche da manuale applicate a Bitcoin dal 2017 al 2026, con lo "
    "stesso costo di 0,12% per operazione. La scala è logaritmica: ogni tacca "
    "moltiplica per dieci. La riga verticale è il risultato di chi ha comprato e "
    "tenuto senza fare nulla. Quattro regole su sei hanno lasciato meno soldi del "
    "non far niente, e una ne ha lasciati meno della metà di quelli iniziali. Due "
    "hanno fatto di più. Nessuna delle sei è stata scelta dopo aver visto il "
    "risultato: sono le sei che i manuali insegnano per prime."
)

#: Chiavi allineate a `cvbook.regole.CATALOGO`: restano in italiano perché sono
#: identificatori del motore di calcolo, non testo mostrato al lettore.
ORDINE = [
    "Forza relativa 30/70",
    "Incrocio 50/200",
    "Sopra la media 200",
    "Incrocio 20/50",
    "Momento a 12 mesi",
    "Rottura a 20 giorni",
]

#: Etichette da mostrare sulla figura, tradotte separatamente dalle chiavi.
ETICHETTE_REGOLA = {
    "Forza relativa 30/70": t("Forza relativa 30/70", "Relative strength 30/70"),
    "Incrocio 50/200": t("Incrocio 50/200", "Crossover 50/200"),
    "Sopra la media 200": t("Sopra la media 200", "Above the 200-day average"),
    "Incrocio 20/50": t("Incrocio 20/50", "Crossover 20/50"),
    "Momento a 12 mesi": t("Momento a 12 mesi", "12-month momentum"),
    "Rottura a 20 giorni": t("Rottura a 20 giorni", "20-day breakout"),
}


def risultati() -> dict[str, dict]:
    df = carica("btcusdt").sort("data")
    p = df["chiusura"].to_numpy()
    fuori = {"Compra e tieni": esegui(p, compra_e_tieni(p), costo=COSTO)}
    for nome in ORDINE:
        fuori[nome] = esegui(p, CATALOGO[nome](p), costo=COSTO)
    for r in fuori.values():
        r["drawdown"] = drawdown_massimo(r["curva"])
    return fuori


def disegna(destinazione: str = "stampa"):
    r = risultati()
    riferimento = r["Compra e tieni"]["finale"]

    valori = [r[n]["finale"] for n in ORDINE]
    y = np.arange(len(ORDINE))

    fig, ax = plt.subplots(figsize=(4.25, 4.25 * 0.62))
    barre = ax.barh(y, valori, height=0.6, facecolor="white", edgecolor="black",
                    linewidth=0.75, hatch="///")
    for b, v in zip(barre, valori):
        if v > riferimento:
            b.set_hatch("")
            b.set_facecolor("#404040")

    ax.axvline(riferimento, color="black", linestyle="--", linewidth=1.0)
    # L'etichetta della riga di riferimento va **dentro** il riquadro: sopra
    # l'ultima barra matplotlib non lascia spazio, e il testo finiva tagliato.
    ax.set_ylim(-0.65, len(ORDINE) - 0.2)
    ax.annotate(t(f"compra e tieni: {num(riferimento, 1)}×", f"buy and hold: {num(riferimento, 1)}×"),
                xy=(riferimento, len(ORDINE) - 0.42), xytext=(4, 0),
                textcoords="offset points", fontsize=6.5, va="center")

    for k, (n, v) in enumerate(zip(ORDINE, valori)):
        ax.annotate(f"{num(v, 1)}×", xy=(v, k), xytext=(3, 0),
                    textcoords="offset points", fontsize=6.5, va="center")

    ax.set_yticks(y)
    ax.set_yticklabels([ETICHETTE_REGOLA[n] for n in ORDINE], fontsize=7)
    ax.set_xscale("log")
    ax.set_xlim(0.3, max(valori) * 3)
    ax.set_xlabel(t("Capitale finale, per ogni euro investito (scala log)",
                     "Final capital, per euro invested (log scale)"))
    ax.grid(axis="y", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTC giornaliero, costi 0,12% per operazione",
                  f"{fonte}, daily BTC, 0.12% cost per trade"), estratto)

    disegna.numeri = {n: (r[n]["finale"], r[n]["operazioni"], r[n]["esposizione"],
                          r[n]["drawdown"]) for n in r}
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} finale {v[0]:8.2f}  op {v[1]:5.0f}  dentro {v[2]:.0%}  dd {v[3]:.1%}")
