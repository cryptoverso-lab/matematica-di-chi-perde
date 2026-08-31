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
from cvbook.stile import firma, num, tacca  # noqa: E402

CAPITOLO = "sec-cap-tecnica"
COSTO = 0.0012
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Sei regole tecniche da manuale applicate a Bitcoin dal 2017 al 2026, con "
    "lo stesso costo di 0,12% per operazione. La scala è logaritmica, e ogni "
    "punto è collegato alla riga verticale — chi ha comprato e non ha più "
    "toccato niente: la lunghezza del segmento è il rapporto fra i due, il "
    "verso dice chi ha fatto meglio. Quattro regole su sei stanno a sinistra, "
    "e una non arriva nemmeno al capitale di partenza. Nessuna delle sei è "
    "stata scelta dopo aver visto il risultato: sono le sei che i manuali "
    "insegnano per prime."
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

    # NIENTE BARRE SU ASSE LOGARITMICO, ed e' il motivo per cui questa figura e'
    # stata rifatta. Una barra codifica il valore con la sua lunghezza, ma su un
    # asse logaritmico lo zero non esiste: le barre partivano dal bordo sinistro
    # del riquadro, cioe' da un punto arbitrario, e la loro lunghezza non voleva
    # dire niente. «Forza relativa 0,5x» e «Incrocio 50/200 4,3x» stanno in
    # rapporto 8,6 a 1 e le barre ne mostravano circa 4 — un rapporto che
    # dipendeva solo da dove cadeva il limite dell'asse. In un capitolo che
    # insegna a diffidare dei grafici, era il grafico da cui diffidare.
    #
    # Al suo posto un segmento che parte dal compra-e-tieni e arriva al valore:
    # su scala logaritmica la sua lunghezza E' il rapporto fra i due, quindi
    # significa qualcosa, e il verso dice a colpo d'occhio chi ha fatto meglio.
    for k, v in enumerate(valori):
        vince = v > riferimento
        ax.plot([riferimento, v], [k, k], color="#8C8C8C", linewidth=0.9,
                linestyle="-", solid_capstyle="butt", zorder=1)
        ax.plot([v], [k], marker="o", markersize=5.2, zorder=2,
                markerfacecolor="#404040" if vince else "white",
                markeredgecolor="black", markeredgewidth=0.9)

    ax.axvline(riferimento, color="black", linestyle="--", linewidth=1.0)
    # L'etichetta della riga di riferimento va **dentro** il riquadro: sopra
    # l'ultima barra matplotlib non lascia spazio, e il testo finiva tagliato.
    ax.set_ylim(-0.65, len(ORDINE) - 0.2)
    ax.annotate(t(f"compra e tieni: {num(riferimento, 1)}×", f"buy and hold: {num(riferimento, 1)}×"),
                xy=(riferimento, len(ORDINE) - 0.42), xytext=(4, 0),
                textcoords="offset points", fontsize=6.5, va="center")

    # Il valore si scrive dalla parte opposta al segmento, altrimenti finisce
    # sopra la linea che collega il punto al riferimento.
    for k, (n, v) in enumerate(zip(ORDINE, valori)):
        verso = 1 if v > riferimento else -1
        ax.annotate(f"{num(v, 1)}×", xy=(v, k), xytext=(7 * verso, 0),
                    textcoords="offset points", fontsize=6.5, va="center",
                    ha="left" if verso > 0 else "right")

    ax.set_yticks(y)
    ax.set_yticklabels([ETICHETTE_REGOLA[n] for n in ORDINE], fontsize=7)
    ax.set_xscale("log")
    ax.set_xlim(0.3, max(valori) * 3)
    # Tacche in multipli, non in notazione scientifica: e' la stessa forma che
    # usa la figura gemella sui mercati azionari, cosi' le due si leggono con
    # lo stesso metro anche se coprono intervalli diversi.
    ax.set_xticks([0.5, 1, 5, 10, 50])
    ax.set_xticklabels([tacca(v, "×") for v in (0.5, 1, 5, 10, 50)])
    ax.grid(which="minor", visible=False)
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
