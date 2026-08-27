"""Cap. 12 — Quante cose diverse ci sono davvero dentro un portafoglio.

L'analisi delle componenti principali risponde a una domanda precisa: quante
direzioni indipendenti servono per descrivere il movimento di un insieme di
asset. Se ne basta una, hai comprato una cosa sola in tre confezioni.

Due panieri a confronto, sugli stessi giorni: tre asset digitali, e gli stessi
tre piu' un indice azionario, un'azione industriale e un cambio. Il numero
effettivo di scommesse passa da una e mezza a quasi quattro — e passa la
soglia operativa del capitolo, che e' due.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-12"
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Analisi delle componenti principali sui rendimenti giornalieri di due "
    "panieri, misurati sugli stessi giorni. A sinistra la varianza spiegata "
    "da ciascuna componente: sui tre asset digitali la prima — una sola "
    "direzione, cioè sostanzialmente «il settore sale o scende» — ne spiega "
    "il 79%; sul paniere che aggiunge indice, azione e cambio la prima scende "
    "al 41%. A destra la varianza cumulata: al paniere digitale bastano due "
    "componenti per superare il 90%, all'altro ne servono cinque. Il numero "
    "effettivo di scommesse passa da 1,55 su tre asset a 3,76 su sei: non è "
    "solo l'effetto di averne aggiunti, perché in quota sale dal 52% al 63% "
    "del massimo possibile."
)


def componenti() -> dict[str, dict]:
    """Quote di varianza e numero effettivo di scommesse, per i due panieri.

    I due panieri si misurano **sugli stessi identici giorni**, ed e' la
    correzione che questa figura ha richiesto. Prima le tre cripto giravano sul
    loro calendario (2.128 giorni) e le sei sull'intersezione con la borsa di
    Milano (1.480): la didascalia prometteva «misurati sugli stessi giorni» e la
    promessa non era mantenuta. Confrontare due decomposizioni fatte su campioni
    diversi non e' sbagliato di poco — e' l'unica cosa che quella figura non
    poteva permettersi, perche' il suo intero contenuto e' un confronto.

    Il calendario comune e' quello del paniere esteso: si prende una volta sola
    e le tre cripto sono le sue prime tre colonne.
    """
    from fig_correlazione_rolling import ESTESO, NOMI, _dati

    _, comune = _dati(ESTESO)
    fuori = {}
    for etichetta, nomi in (("tre asset digitali", NOMI),
                            ("con indice, azione e cambio", ESTESO)):
        M = comune[:, :len(nomi)]
        C = np.corrcoef(M.T)
        valori = np.linalg.eigvalsh(C)[::-1]
        quote = valori / valori.sum()
        fuori[etichetta] = {
            "asset": len(nomi),
            "quote": quote * 100,
            "cumulata": np.cumsum(quote) * 100,
            "effettivo": float(1 / np.sum(quote**2)),
            "correlazione": float(C[np.triu_indices(len(nomi), 1)].mean()),
        }
    return fuori


def disegna(destinazione: str = "stampa"):
    dati = componenti()
    stili = [("#404040", "", "-", "o"), ("white", "///", "--", "s")]

    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"))

    larghezza = 0.38
    for j, ((etichetta, d), (colore, retino, tratto, marcatore)) in enumerate(
        zip(dati.items(), stili)
    ):
        x = np.arange(1, len(d["quote"]) + 1) + (j - 0.5) * larghezza
        sx.bar(x, d["quote"], width=larghezza, facecolor=colore, edgecolor="black",
               linewidth=0.75, hatch=retino, label=f"{d['asset']} {t('asset', 'assets')}")
        # L'etichetta della prima componente va dalla parte esterna della
        # propria barra, non centrata su di essa: le due barre della prima
        # componente sono alte 79% e 41%, e la scritta della piu' bassa,
        # centrata, finiva per meta' sopra il pieno scuro di quella accanto —
        # la prima cifra spariva.
        # The first-component label sits on the outer side of its own bar: the
        # two bars are 79% and 41% tall, and the shorter one's centred label
        # had half of itself over the neighbouring dark fill.
        verso = "right" if j == 0 else "left"
        sx.annotate(f"{d['quote'][0]:.0f}%", xy=(x[0], d["quote"][0]),
                    xytext=(-2 if j == 0 else 2, 3), textcoords="offset points",
                    ha=verso, fontsize=6.5)

        dx.plot(np.arange(1, len(d["cumulata"]) + 1), d["cumulata"], color="black",
                linestyle=tratto, linewidth=1.2, marker=marcatore, markersize=3.0,
                markerfacecolor=colore, markeredgecolor="black",
                label=t(f"{num(d['effettivo'], 2)} scommesse su {d['asset']}",
                         f"{num(d['effettivo'], 2)} bets on {d['asset']}"))

    sx.set_xticks(np.arange(1, 7))
    sx.set_xlabel(t("Componente", "Component"))
    sx.set_ylabel(t("Varianza spiegata (%)", "Variance explained (%)"))
    sx.set_ylim(0, 92)
    sx.grid(axis="x", visible=False)
    sx.legend(loc="upper right", fontsize=6.0)

    dx.axhline(90, color="#595959", linestyle=":", linewidth=0.9)
    dx.annotate("90%", xy=(1, 90), xytext=(2, 4), textcoords="offset points", fontsize=6.5)
    dx.set_xticks(np.arange(1, 7))
    dx.set_xlabel(t("Componenti usate", "Components used"))
    dx.set_ylabel(t("Varianza cumulata (%)", "Cumulative variance (%)"))
    dx.set_ylim(35, 104)
    dx.legend(loc="lower right", fontsize=6.0, title=t("numero effettivo", "effective number"),
              title_fontsize=6.0)

    fonte, estratto = citazione("btcusdt")
    firma(fig, f"{fonte} e Yahoo Finance, rendimenti giornalieri", estratto)

    disegna.numeri = dati
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for etichetta, d in disegna.numeri.items():
        quote = ", ".join(f"{q:.1f}%" for q in d["quote"])
        print(f"\n{etichetta} ({d['asset']} asset)")
        print(f"  quote: {quote}")
        print(f"  cumulata: {', '.join(f'{c:.1f}%' for c in d['cumulata'])}")
        print(f"  correlazione media {d['correlazione']:.4f}")
        print(f"  numero effettivo {d['effettivo']:.3f}"
              f"  ({d['effettivo'] / d['asset']:.1%} del massimo)")
