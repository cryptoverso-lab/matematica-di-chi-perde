"""Cap. 13 — Piu' parametri, migliore il passato, peggiore il futuro.

La ricerca riproduce cio' che si fa davvero quando si costruisce un metodo: si
parte dalla condizione migliore, e poi si aggiunge ogni volta quella che
migliora di piu' il risultato sui dati che si stanno guardando. E' la
costruzione per aggiunte successive descritta dal capitolo, non un'estrazione a
caso — ed e' per questo che la curva sul passato sale a ogni passo, per
costruzione.

Le condizioni sono rumore puro: non contengono alcuna informazione. Tutto cio'
che la curva superiore guadagna e' rumore memorizzato, e la curva sui dati mai
visti lo dimostra.

I COSTI NON SONO INCLUSI, ed e' una scelta dichiarata invece che una svista.
Questa figura non misura un risultato: misura di quanto sale una curva quando
si sceglie, fra quattrocento numeri casuali, quello che la fa salire di piu'.
Una regola costruita cosi' cambia posizione quasi ogni giorno; addebitandole
lo 0,12% a movimento nessuna delle quattrocento supererebbe il capitale
iniziale, la ricerca non avrebbe nulla da selezionare e l'effetto da mostrare
sparirebbe insieme al suo oggetto. La didascalia lo dice in pagina.
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
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-13"
CONDIZIONI_MAX = 25
DISPONIBILI = 400
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Una regola costruita per aggiunte successive: a ogni passo entra, fra "
    "quattrocento condizioni disponibili, quella che migliora di più il "
    "risultato sulla prima metà della storia, e ci si ferma quando nessuna "
    "aggiunta migliora più nulla. Le condizioni sono numeri casuali: non "
    "contengono alcuna informazione. I costi non sono inclusi, ed è "
    "dichiarato: qui si misura un effetto di selezione, non un risultato — "
    "con i costi nessuna delle quattrocento supererebbe il capitale iniziale "
    "e non ci sarebbe nulla da selezionare. La curva sul passato sale a ogni "
    "passo, da 31 a 2.190 volte il capitale in dodici aggiunte. Quella sui "
    "dati mai visti tocca il massimo alla quinta e da lì peggiora, chiudendo "
    "a 1,5 volte. Fra le due curve c'è rumore memorizzato — e chi guarda solo "
    "la prima non ha modo di distinguerlo da una scoperta."
)


def ricerca_per_aggiunte(dentro: np.ndarray, fuori: np.ndarray, rumore: np.ndarray,
                         passi: int) -> tuple[list[float], list[float]]:
    """Selezione ingenua in avanti: a ogni passo la condizione che migliora di piu'."""
    meta = len(dentro)

    def valuta(segnale: np.ndarray, r: np.ndarray) -> float:
        return float(np.prod(1 + segnale * r))

    scelte: set[int] = set()
    somma = np.zeros(rumore.shape[1])
    corrente = 0.0
    curva_dentro, curva_fuori = [], []

    for _ in range(passi):
        migliore_indice, migliore_valore = None, -np.inf
        for k in range(len(rumore)):
            if k in scelte:
                continue
            segnale = ((somma + rumore[k]) > 0).astype(float)
            valore = valuta(segnale[:meta], dentro)
            if valore > migliore_valore:
                migliore_indice, migliore_valore = k, valore

        # Ci si ferma quando nessuna aggiunta migliora: e' cio' che fa chiunque
        # costruisca un metodo per tentativi, ed e' la ragione per cui la curva
        # sale sempre. Nessuno aggiunge un ingrediente che peggiora il risultato
        # che sta guardando.
        if migliore_valore <= corrente:
            break

        scelte.add(migliore_indice)
        somma = somma + rumore[migliore_indice]
        corrente = migliore_valore
        segnale = (somma > 0).astype(float)
        curva_dentro.append(migliore_valore)
        curva_fuori.append(valuta(segnale[meta:], fuori))

    return curva_dentro, curva_fuori


def disegna(destinazione: str = "stampa"):
    r = rendimenti(carica("btcusdt").sort("data")["chiusura"].to_numpy())
    meta = len(r) // 2
    dentro, fuori = r[:meta], r[meta:]

    rng = np.random.default_rng(seed_for("dimensionalita"))
    rumore = rng.normal(size=(DISPONIBILI, len(r)))

    dentro_curva, fuori_curva = ricerca_per_aggiunte(dentro, fuori, rumore, CONDIZIONI_MAX)
    x = np.arange(1, len(dentro_curva) + 1)

    fig, ax = plt.subplots()
    ax.plot(x, dentro_curva, color="black", linestyle="-", linewidth=1.3,
            marker="o", markersize=2.6)
    ax.plot(x, fuori_curva, color="#8C8C8C", linestyle="--", linewidth=1.3,
            marker="s", markersize=2.6)
    ax.axhline(1.0, color="black", linestyle=":", linewidth=0.8)

    ax.text(0.03, 0.95, t("sui dati usati per costruire", "on the data used to build"),
            transform=ax.transAxes, fontsize=7, va="top")
    ax.text(0.03, 0.87, t("sui dati mai visti", "on data never seen"), transform=ax.transAxes,
            fontsize=7, color="#595959", va="top")

    ax.set_yscale("log")
    ax.set_xlabel(t("Condizioni aggiunte alla regola", "Conditions added to the rule"))
    ax.set_ylabel(t("Capitale finale (× iniziale)", "Final capital (× starting)"))

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT — condizioni generate casualmente",
                  f"{fonte}, BTCUSDT — randomly generated conditions"), estratto)

    disegna.numeri = {
        "dentro_1": dentro_curva[0],
        "dentro_max": dentro_curva[-1],
        "fuori_1": fuori_curva[0],
        "fuori_max": fuori_curva[-1],
        "fuori_migliore": max(fuori_curva),
        "passo_migliore_fuori": int(np.argmax(fuori_curva)) + 1,
        "monotona": all(a <= b + 1e-9 for a, b in zip(dentro_curva, dentro_curva[1:])),
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} {v}")
