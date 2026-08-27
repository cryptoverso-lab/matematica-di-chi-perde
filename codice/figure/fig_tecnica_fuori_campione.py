"""Cap. analisi tecnica — Le stesse sei regole su un mercato indipendente.

Il capitolo dichiarava una lacuna: due conferme su mercati digitali valgono
poco piu' di una, e mancava la prova su un mercato che non si muove insieme
alle cripto. Questa figura la fa, con lo stesso protocollo dichiarato prima:
stesse sei regole, stesso costo, stesso sfasamento di un giorno, e si stampano
tutti e sei i risultati.

Le finestre restano quelle dei manuali, con una sola correzione dichiarata: il
momento e' definito in **mesi**, e dodici mesi su una borsa che chiude nel fine
settimana sono circa 252 barre, non 365.
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
from cvbook.regole import (  # noqa: E402
    BARRE_ANNO_BORSA,
    catalogo,
    compra_e_tieni,
    esegui,
)
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-tecnica"
COSTO = 0.0012
SERIE = "ftsemib"
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Le stesse sei regole, stesso costo e stesso protocollo, applicate "
    "all'indice della borsa italiana dal 2000 al 2026. Stessa codifica della "
    "figura precedente — punto collegato al proprio compra-e-tieni — e stesso "
    "ordine delle regole, così il rimescolamento si vede a colpo d'occhio: la "
    "rottura a venti giorni, che là era la migliore con 35,7 volte il "
    "capitale, qui è una delle due che perdono soldi. La forza relativa, che "
    "là dimezzava il capitale, qui batte il non far niente — ma l'indice è di "
    "prezzo e non incorpora i dividendi, quindi il suo compra-e-tieni è "
    "sottostimato e diverse delle regole che qui lo battono, contati quelli, "
    "non lo batterebbero: il capitolo lo misura poco sotto, su un titolo con "
    "i prezzi aggiustati. Le due figure coprono intervalli diversi perché i "
    "due mercati sono andati diversamente: quello che si confronta è "
    "l'ordine, non l'altezza. Nessuna regola è stata scelta dopo aver visto "
    "il risultato."
)

#: Lo stesso ordine della figura su Bitcoin: è ciò che rende leggibile il
#: rimescolamento. Se cambia là, cambia qui. Restano in italiano perché sono
#: chiavi allineate a `cvbook.regole.catalogo()`, non testo per il lettore.
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


def risultati(serie: str = SERIE) -> dict[str, dict]:
    df = carica(serie).sort("data")
    p = df["chiusura"].to_numpy()
    regole = catalogo(BARRE_ANNO_BORSA)
    fuori = {"Compra e tieni": esegui(p, compra_e_tieni(p), costo=COSTO)}
    for nome in ORDINE:
        fuori[nome] = esegui(p, regole[nome](p), costo=COSTO)
    for r in fuori.values():
        r["drawdown"] = drawdown_massimo(r["curva"])
    return fuori


def disegna(destinazione: str = "stampa"):
    r = risultati()
    riferimento = r["Compra e tieni"]["finale"]

    valori = [r[n]["finale"] for n in ORDINE]
    y = np.arange(len(ORDINE))

    fig, ax = plt.subplots(figsize=(4.25, 4.25 * 0.62))
    # Stessa codifica della figura gemella su Bitcoin, e per la stessa ragione:
    # su un asse logaritmico una barra non ha un'origine, quindi la sua
    # lunghezza non dice niente. Il segmento parte dal compra-e-tieni di QUESTO
    # mercato e arriva al valore: la lunghezza e' il rapporto fra i due. Le due
    # figure coprono intervalli diversi perche' i mercati sono diversi — cio'
    # che il capitolo mette a confronto e' l'ordine delle regole, e con questa
    # codifica si legge alla stessa maniera in entrambe.
    for k, v in enumerate(valori):
        vince = v > riferimento
        ax.plot([riferimento, v], [k, k], color="#8C8C8C", linewidth=0.9,
                linestyle="-", solid_capstyle="butt", zorder=1)
        ax.plot([v], [k], marker="o", markersize=5.2, zorder=2,
                markerfacecolor="#404040" if vince else "white",
                markeredgecolor="black", markeredgewidth=0.9)

    ax.axvline(riferimento, color="black", linestyle="--", linewidth=1.0)
    ax.set_ylim(-0.65, len(ORDINE) - 0.2)
    ax.annotate(t(f"compra e tieni: {num(riferimento, 2)}×", f"buy and hold: {num(riferimento, 2)}×"),
                xy=(riferimento, len(ORDINE) - 0.42), xytext=(4, 0),
                textcoords="offset points", fontsize=6.5, va="center")

    for k, v in enumerate(valori):
        verso = 1 if v > riferimento else -1
        ax.annotate(f"{num(v, 2)}×", xy=(v, k), xytext=(7 * verso, 0),
                    textcoords="offset points", fontsize=6.5, va="center",
                    ha="left" if verso > 0 else "right")

    ax.set_yticks(y)
    ax.set_yticklabels([ETICHETTE_REGOLA[n] for n in ORDINE], fontsize=7)
    ax.set_xscale("log")
    ax.set_xlim(0.4, 5.5)
    # Su un intervallo cosi' stretto le tacche automatiche di un asse
    # logaritmico escono in notazione scientifica: qui si scrivono a mano.
    ax.set_xticks([0.5, 1, 2, 3, 5])
    ax.set_xticklabels(["0,5×", "1×", "2×", "3×", "5×"])
    ax.set_xticks([], minor=True)
    ax.set_xlabel(t("Capitale finale, per ogni euro investito (scala log)",
                     "Final capital, per euro invested (log scale)"))
    ax.grid(axis="y", visible=False)

    fonte, estratto = citazione(SERIE)
    firma(fig, t(f"{fonte}, FTSE MIB giornaliero, costi 0,12% per operazione",
                  f"{fonte}, daily FTSE MIB, 0.12% cost per trade"), estratto)

    disegna.numeri = {n: (r[n]["finale"], r[n]["operazioni"], r[n]["esposizione"],
                          r[n]["drawdown"]) for n in r}
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    for serie in (SERIE, "eni"):
        print(f"\n{serie}")
        for k, v in risultati(serie).items():
            print(f"  {k:22s} finale {v['finale']:7.2f}  op {v['operazioni']:5.0f}"
                  f"  dentro {v['esposizione']:.0%}  dd {v['drawdown']:.1%}")
    with contesto("stampa"):
        disegna()
