"""Cap. 15 — Il metro: rispetto a cosa si giudica un risultato.

Una strategia semplice viene confrontata non con lo zero, ma con mille
strategie che entrano ed escono negli stessi giorni scelti a caso, con lo
stesso numero di operazioni e gli stessi costi. E' l'unico confronto che
risponde alla domanda giusta: sarebbe bastato il caso?
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
from cvbook.regole import esegui, sopra_media  # noqa: E402
from cvbook.stile import firma, num, tacca  # noqa: E402

CAPITOLO = "sec-cap-15"
FINESTRA = 50
COSTO = 0.0012
N_CASUALI = 1000
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Risultato di mille strategie che stanno dentro al mercato negli stessi "
    "giorni complessivi della strategia vera, ma scelti a caso, con lo stesso "
    "numero di entrate e uscite e gli stessi costi. La linea verticale è il "
    "risultato della strategia vera. La domanda a cui questa figura risponde "
    "non è «ha guadagnato?» ma «ha fatto meglio del semplice essere stato "
    "dentro per altrettanto tempo?»."
)


def disegna(destinazione: str = "stampa"):
    p = carica("btcusdt").sort("data")["chiusura"].to_numpy()

    # La regola e i costi vengono da `cvbook.regole`, cioe' dallo stesso motore
    # che usano il testo e i quaderni: se un numero cambia qui, cambia ovunque.
    segnale = sopra_media(p, FINESTRA)
    conto = esegui(p, segnale, costo=COSTO)

    def risultato(s: np.ndarray) -> float:
        return esegui(p, s, costo=COSTO)["finale"]

    vera = conto["finale"]
    giorni_dentro = int(segnale.sum())
    cambi = int(conto["operazioni"])

    # Il confronto deve essere equo: le strategie casuali devono avere lo stesso
    # numero di giorni dentro E lo stesso numero di operazioni, altrimenti pagano
    # costi diversi e il confronto e' truccato. Si costruiscono quindi come
    # blocchi contigui, non come giorni sparsi.
    #
    # ATTENZIONE, ed e' il motivo per cui questa funzione e' scritta cosi'.
    # La versione precedente estraeva le posizioni di partenza dei blocchi in
    # modo indipendente dalle loro lunghezze: due blocchi potevano sovrapporsi,
    # e la sovrapposizione veniva riassorbita silenziosamente dall'assegnazione,
    # lasciando MENO giorni dentro e MENO operazioni di quelli dichiarati. Il
    # metro risultava sbilanciato a favore della strategia vera su un asset
    # salito 13,7 volte — esattamente il difetto che questo capitolo insegna a
    # cercare negli altrui backtest. Adesso il vincolo e' costruttivo: si
    # ripartiscono i giorni DENTRO in n_blocchi tratti e i giorni FUORI negli
    # n_blocchi+1 intervalli fra un tratto e l'altro, poi si alternano. Somme
    # esatte per costruzione, nessuna sovrapposizione possibile.
    n_blocchi = max(cambi // 2, 1)
    n_fuori = len(p) - giorni_dentro
    rng = np.random.default_rng(seed_for("metro-del-caso"))

    def _ripartisci(totale: int, parti: int, minimo: int) -> np.ndarray:
        """Divide `totale` in `parti` addendi casuali, ciascuno >= `minimo`."""
        libero = totale - minimo * parti
        if parti == 1:
            return np.array([totale])
        tagli = np.sort(rng.integers(0, libero + 1, size=parti - 1))
        return np.diff(np.concatenate([[0], tagli, [libero]])) + minimo

    casuali = []
    for _ in range(N_CASUALI):
        s = np.zeros(len(p))
        dentro = _ripartisci(giorni_dentro, n_blocchi, 1)
        # Tutti i vuoti, compresi quello iniziale e quello finale, devono essere
        # >= 1: due tratti che si toccano contano come una sola operazione
        # invece di due, e un tratto attaccato a un bordo della serie ne perde
        # una perche' non ha l'entrata (o l'uscita) da pagare.
        fuori = _ripartisci(n_fuori, n_blocchi + 1, 1)
        pos = 0
        for i in range(n_blocchi):
            pos += int(fuori[i])
            s[pos:pos + int(dentro[i])] = 1.0
            pos += int(dentro[i])
        assert int(s.sum()) == giorni_dentro
        assert int(esegui(p, s, costo=COSTO)["operazioni"]) == 2 * n_blocchi
        casuali.append(risultato(s))
    casuali = np.array(casuali)

    fig, ax = plt.subplots()
    # Classi a passo logaritmico, perche' l'asse lo e': con classi a passo
    # lineare la prima copriva da sola due decadi e l'istogramma diventava un
    # muro a sinistra seguito dal nulla.
    classi = np.logspace(np.log10(casuali.min()), np.log10(casuali.max()), 40)
    ax.hist(casuali, bins=classi, facecolor="white", edgecolor="black",
            linewidth=0.7, hatch="///")
    # La verticale della strategia vera era un tratto pieno che si fermava al
    # 94% dell'asse: alla stessa altezza delle barre e con lo stesso disegno,
    # veniva letta come una barra dell'istogramma — e per giunta come la piu'
    # alta, cioe' come la classe piu' numerosa. Adesso e' tratteggiata e
    # attraversa tutto il riquadro: e' un riferimento, non un dato.
    ax.axvline(vera, color="black", linewidth=1.6, linestyle=(0, (4, 2)))

    percentile = (casuali < vera).mean() * 100
    ax.annotate(
        t(f"la strategia vera: {num(vera, 1)}×\nmeglio del {num(percentile, 1)}% dei casi",
          f"the real strategy: {num(vera, 1)}×\nbetter than {num(percentile, 1)}% of the cases"),
        xy=(vera, 0),
        xytext=(8, 70),
        textcoords="offset points",
        fontsize=7,
        linespacing=1.35,
        arrowprops=dict(arrowstyle="->", linewidth=0.75, color="black"),
    )
    ax.text(0.02, 0.96,
            t(f"{num(N_CASUALI)} strategie casuali · {num(giorni_dentro)} giorni dentro · "
              f"{num(cambi)} operazioni",
              f"{num(N_CASUALI)} random strategies · {num(giorni_dentro)} days in market · "
              f"{num(cambi)} trades"),
            transform=ax.transAxes, fontsize=6.5, va="top")

    ax.set_xlabel(t("Capitale finale (× iniziale)", "Final capital (× starting)"))
    ax.set_ylabel(t("Numero di strategie casuali", "Number of random strategies"))
    ax.set_xscale("log")
    ax.set_xticks([0.1, 1, 10, 100])
    ax.set_xticklabels([tacca(v, "×") for v in (0.1, 1, 10, 100)])
    ax.set_ylim(0, max(np.histogram(casuali, bins=classi)[0]) * 1.28)
    ax.grid(which="minor", visible=False)

    fonte, estratto = citazione("btcusdt")
    # «per operazione», non «per giro»: il motore addebita il costo a ogni
    # variazione di posizione, quindi un giro completo — entrata piu' uscita —
    # ne paga due. La firma diceva il contrario e dimezzava i costi dichiarati.
    firma(fig, t(f"{fonte}, BTCUSDT — costi dello 0,12% per operazione",
                  f"{fonte}, BTCUSDT — 0.12% cost per trade"), estratto)

    disegna.numeri = {
        "vera": vera,
        "giorni_dentro": giorni_dentro,
        "operazioni": cambi,
        "mediana_casuali": float(np.median(casuali)),
        "percentile": float(percentile),
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:18s} {v}")
