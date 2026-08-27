"""Cap. 23 — Cosa succede quando puoi provare mille idee in un pomeriggio.

Piu' tentativi si fanno, piu' strategie "funzionanti" si trovano: cresce senza
limite, perche' e' un effetto del cercare, non del trovare. La quota che
sopravvive fuori campione, invece, resta inchiodata al livello del caso.

I COSTI NON SONO INCLUSI, come nella figura gemella del cap. 13, e per la
stessa ragione: le regole sono soglie su rumore e cambiano posizione quasi ogni
giorno. Con i costi nessuna supererebbe il capitale iniziale sulla prima meta',
il filtro non promuoverebbe nessuno e la domanda del pannello destro — di
quelle promosse, che quota regge? — resterebbe senza denominatore. Qui si
misura un effetto di selezione, non un risultato, e la didascalia lo dichiara.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook import seed_for  # noqa: E402
from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t as tr  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-23"
TENTATIVI = [10, 50, 100, 500, 1000, 2000]
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Regole generate a caso e valutate sulla prima metà della storia: si "
    "tengono quelle che superano il capitale iniziale — senza costi, come "
    "nella figura del @sec-cap-13 e per la stessa ragione: qui si misura un "
    "effetto di selezione, non un risultato. A sinistra, quante ne "
    "«funzionano»: il numero cresce insieme ai tentativi, perché trovarle è "
    "una conseguenza del cercare — e cresce anche quello di chi regge sulla "
    "seconda metà mai vista, per la stessa ragione. A destra la domanda che "
    "conta: di quelle promosse, che **quota** regge fuori campione? La linea "
    "si appiattisce esattamente sul livello che si otterrebbe promuovendo a "
    "caso, senza guardare niente: 69%. Selezionare non ha aggiunto "
    "informazione, ha solo prodotto più candidati."
)


def disegna(destinazione: str = "stampa"):
    r = rendimenti(carica("btcusdt")["chiusura"].to_numpy())
    meta = len(r) // 2
    rng = np.random.default_rng(seed_for("velocita-illusione"))

    massimo = max(TENTATIVI)
    dentro = np.empty(massimo)
    fuori = np.empty(massimo)

    for k in range(massimo):
        # Una "idea" è una regola di esposizione generata a caso: nessuna
        # informazione, ma nemmeno meno sensata di molte regole vere.
        soglia = rng.uniform(-0.6, 0.6)
        rumore = rng.normal(size=len(r))
        segnale = (rumore > soglia).astype(float)
        dentro[k] = np.prod(1 + segnale[:meta] * r[:meta])
        fuori[k] = np.prod(1 + segnale[meta:] * r[meta:])

    trovate, sopravvissute, quota = [], [], []
    for n in TENTATIVI:
        ok = dentro[:n] > 1.0
        regge = ok & (fuori[:n] > 1.0)
        trovate.append(int(ok.sum()))
        sopravvissute.append(int(regge.sum()))
        # LA QUOTA E' LA TESI, e il conteggio da solo diceva il contrario.
        # Il pannello di sinistra mostra due rette parallele che salgono: chi lo
        # guardava leggeva «piu' ne provi, piu' ne trovi che reggono davvero»,
        # cioe' l'opposto del capitolo. Un conteggio assoluto cresce sempre con
        # i tentativi, per costruzione. La domanda vera e' che FRAZIONE delle
        # promosse sopravvive, e quella non si muove.
        quota.append(100.0 * regge.sum() / max(ok.sum(), 1))

    # Livello di riferimento: la frazione di regole che reggono fuori campione
    # SENZA aver superato alcuna selezione. Se la quota selezionata ci sta
    # sopra, la selezione non ha aggiunto informazione.
    caso = 100.0 * float((fuori > 1.0).mean())

    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"))

    sx.plot(TENTATIVI, trovate, color="black", linestyle="-", linewidth=1.3,
            marker="o", markersize=3)
    sx.plot(TENTATIVI, sopravvissute, color="#8C8C8C", linestyle="--", linewidth=1.3,
            marker="s", markersize=3)
    sx.text(0.04, 0.94, tr("«funzionano» dove le hai cercate",
                           "“work” where you looked for them"),
            transform=sx.transAxes, fontsize=6.5, va="top")
    sx.text(0.04, 0.86, tr("reggono anche fuori", "hold up out of sample"),
            transform=sx.transAxes, fontsize=6.5, color="#595959", va="top")
    sx.set_xscale("log")
    sx.set_yscale("log")
    sx.set_xlabel(tr("Idee provate", "Ideas tried"))
    sx.set_ylabel(tr("Quante ne trovi (scala log.)", "How many you find (log scale)"))
    # Tacche a decadi: mettendone una per ogni valore provato, «1.000» e «2.000»
    # finivano una sull'altra. Migliaia col punto, come nel resto del libro.
    sx.set_xticks([10, 100, 1000])
    sx.set_xticklabels(["10", "100", "1.000"])
    sx.set_yticks([10, 100, 1000])
    sx.set_yticklabels(["10", "100", "1.000"])
    sx.grid(which="minor", visible=False)

    dx.plot(TENTATIVI, quota, color="black", linestyle="-", linewidth=1.3,
            marker="o", markersize=3)
    dx.axhline(caso, color="#595959", linestyle=(0, (1, 2)), linewidth=0.9)
    dx.annotate(
        tr(f"promuovendo a caso: {caso:.0f}%", f"promoting at random: {caso:.0f}%"),
        xy=(TENTATIVI[0], caso), xytext=(0, -12), textcoords="offset points",
        fontsize=6.5, color="#595959", ha="left", va="top",
    )
    dx.set_xscale("log")
    dx.set_ylim(0, 100)
    dx.set_xlabel(tr("Idee provate", "Ideas tried"))
    dx.set_ylabel(tr("Di quelle promosse, quante reggono (%)",
                     "Of those promoted, how many hold up (%)"))
    dx.set_xticks([10, 100, 1000])
    dx.set_xticklabels(["10", "100", "1.000"])
    dx.grid(which="minor", visible=False)

    disegna.numeri = {"quota": quota, "caso": caso,
                      "trovate": trovate, "sopravvissute": sopravvissute}

    fonte, estratto = citazione("btcusdt")
    firma(fig, tr(f"{fonte}, BTCUSDT — regole generate casualmente",
                   f"{fonte}, BTCUSDT — randomly generated rules"), estratto)
    return fig
