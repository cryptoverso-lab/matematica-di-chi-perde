"""Cap. 16 — Lo stesso identico test, con e senza un errore di una riga.

La versione sbagliata decide oggi usando il prezzo di chiusura di oggi, che
al momento della decisione non e' ancora noto. E' l'errore piu' comune di
tutti, produce curve spettacolari, e si vede solo se lo si cerca.

Le due regole vengono da `cvbook.regole` e differiscono per una sola chiamata,
`_ritarda`: e' il modo di rendere verificabile l'affermazione del capitolo —
«la differenza e' una riga di codice». I costi ci sono in tutte e tre le curve,
compreso il compra-e-tieni, perche' un backtest a costo zero questo libro lo
chiama falso due capitoli prima.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.regole import (  # noqa: E402
    compra_e_tieni,
    esegui,
    sopra_media,
    sopra_media_con_lookahead,
)
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-16"
FINESTRA = 20
COSTO = 0.0012
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "La stessa regola — restare investiti quando il prezzo chiude sopra la "
    "sua media a venti giorni — calcolata in due modi, con gli stessi costi "
    "dello 0,12% per operazione. Nella versione causale il confronto usa la "
    "chiusura di oggi e la posizione vale **da domani**. In quella con "
    "lookahead la posizione di oggi incassa già il movimento di oggi: al "
    "momento in cui la decisione andava presa, quella chiusura non esisteva. "
    "Fra le due manca una sola chiamata — lo sfasamento di un giorno — e vale "
    "un fattore trecentottantamila."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt").sort("data")
    date = df["data"].to_list()
    p = df["chiusura"].to_numpy()

    causale = esegui(p, sopra_media(p, FINESTRA), costo=COSTO)
    futuro = esegui(p, sopra_media_con_lookahead(p, FINESTRA), costo=COSTO)
    tieni = esegui(p, compra_e_tieni(p), costo=COSTO)

    fig, ax = plt.subplots()
    ax.plot(date, futuro["curva"], color="black", linestyle="-", linewidth=1.3)
    ax.plot(date, causale["curva"], color="#595959", linestyle="--", linewidth=1.2)
    ax.plot(date, tieni["curva"], color="#B0B0B0", linestyle=":", linewidth=1.1)
    ax.set_yscale("log")

    for y, testo, colore in [
        (0.95, t(f"con lookahead — {num(futuro['finale'])}×",
                  f"with lookahead — {num(futuro['finale'])}×"), "black"),
        (0.88, t(f"causale — {num(causale['finale'], 1)}×",
                  f"causal — {num(causale['finale'], 1)}×"), "#595959"),
        (0.81, t(f"compra e tieni — {num(tieni['finale'], 1)}×",
                  f"buy and hold — {num(tieni['finale'], 1)}×"), "#8C8C8C"),
    ]:
        ax.text(0.02, y, testo, transform=ax.transAxes, fontsize=7, color=colore, va="top")

    ax.set_ylabel(t("Capitale (× iniziale, scala log.)", "Capital (× starting, log scale)"))
    # Tacche in multipli, non in notazione scientifica: «10⁶» e' una barriera
    # gratuita per il lettore a cui questo libro parla, ed e' la stessa scelta
    # fatta su tutte le altre figure con asse logaritmico.
    ax.set_yticks([1, 100, 10_000, 1_000_000])
    ax.set_yticklabels(["1×", "100×", "10.000×", t("1 milione ×", "1 million ×")])
    ax.grid(which="minor", visible=False)
    fig.autofmt_xdate(rotation=0, ha="center")

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero — costi dello 0,12% per operazione",
                  f"{fonte}, daily BTCUSDT — 0.12% cost per trade"), estratto)

    disegna.numeri = {
        "futuro": futuro["finale"],
        "causale": causale["finale"],
        "compra_e_tieni": tieni["finale"],
        "operazioni_causale": causale["operazioni"],
        "rapporto": futuro["finale"] / causale["finale"],
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} {v:,.2f}")
