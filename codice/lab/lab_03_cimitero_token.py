# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Lab 3 — Il cimitero dei token
#
# *Quaderno del capitolo «Il cimitero dei token» di **La matematica di chi perde**.*
#
# Questo quaderno contiene i prezzi veri dei due asset morti di cui parla il
# capitolo — uno andato a zero in nove giorni, uno il cui mercato è stato chiuso.
# Conservare quei dati è più difficile di quanto sembri: la maggior parte delle
# fonti comode espone **solo ciò che è ancora attivo**.
#
# Il valore del quaderno non è la cronologia del crollo. È l'ultimo esercizio:
# ricostruire lo stesso paniere guardando solo i sopravvissuti, e vedere che
# risposta tranquillizzante si ottiene.
#
# ---
#
# > **EN** — *Lab 3 — The graveyard of tokens.* Notebook for the chapter "The
# > graveyard of tokens". This notebook contains the real prices of the two
# > dead assets the chapter talks about — one that went to zero in nine days,
# > one whose market was shut down. Keeping that data is harder than it
# > sounds: most convenient sources expose **only what's still active**. The
# > notebook's value isn't the timeline of the crash. It's the final
# > exercise: rebuilding the same basket looking only at the survivors, and
# > seeing what reassuring answer you get.

# %% [markdown]
# Le righe marcate **PROVA** sono quelle da cambiare: cambiale e riesegui per
# vedere l'effetto. Il resto — comprese le righe marcate **NON TOCCARE** —
# serve a mantenere il risultato confrontabile con quello stampato nel libro.
#
# The lines marked **TRY** are the ones to change: edit them and rerun to see
# the effect. Everything else — including lines marked **DO NOT CHANGE** —
# exists to keep the result comparable with the one printed in the book.

# %%
# Setup — esegui questa cella per prima.
# %pip install -q "polars>=1.0"
try:
    import avvio
except ModuleNotFoundError:
    import urllib.request

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/cryptoverso-lab/matematica-di-chi-perde/main/codice/lab/avvio.py",
        "avvio.py",
    )
    import avvio

avvio.prepara(["btcusdt", "ethusdt", "solusdt", "lunausdt", "fttusdt"])

# %%
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from cvbook.dati import DISCONTINUITA, carica, carica_strumento
from cvbook.metriche import recupero_necessario

# %% [markdown]
# ## 1. Nove giorni
#
# Scala logaritmica: ogni tacca vale un fattore dieci. Su scala lineare questo
# grafico sarebbe una riga verticale seguita da una riga piatta — ed è esattamente
# così che i crolli appaiono a chi li guarda mentre accadono.
#
# La serie si ferma il **13 maggio 2022**, ed è il punto più importante di questa
# cella. Dal 31 maggio lo stesso identificativo, sullo stesso mercato, quota
# un'altra cosa: LUNA 2.0, un progetto nuovo lanciato dopo il crollo. Chi disegna
# la serie per intero ottiene un grafico che scende a 0,00005 e poi risale di
# centomila volte — e chi lo guarda conclude l'esatto contrario di quello che è
# successo. La data del taglio non è scritta qui: sta nel registro dei dati
# (`cvbook.dati.DISCONTINUITA`), che è l'unico posto in cui vive.
#
# ---
#
# > **EN** — *1. Nine days.* Logarithmic scale: each tick is a factor of ten.
# > On a linear scale this chart would be a vertical line followed by a flat
# > line — and that's exactly how crashes look to whoever watches them
# > happen. The series stops on **13 May 2022**: from the 31st the same ticker
# > quotes a different token. Drawing the whole series shows a resurrection
# > that nobody lived.

# %%
luna = carica_strumento("lunausdt").sort("data").filter(pl.col("data") >= dt.date(2022, 4, 1))

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.semilogy(luna["data"].to_list(), luna["chiusura"].to_numpy(), linewidth=1.6)
    ax.set_ylabel("Prezzo di chiusura (USDT, scala log)")
    fig.autofmt_xdate()
    plt.show()

# %% [markdown]
# ### Provalo tu: il grafico che racconta il contrario
#
# Esegui la cella qui sotto. È la stessa serie, letta grezza — con dentro il
# ticker riusato — fino al 30 giugno. È il grafico che troveresti su quasi
# qualunque archivio, ed è quello che il capitolo ti chiede di **non** credere.
#
# ---
#
# > **EN** — *Try it: the chart that says the opposite.* Run the cell below.
# > Same series, read raw — reused ticker included — through 30 June.

# %%
grezza = carica("lunausdt").sort("data").filter(
    pl.col("data").is_between(dt.date(2022, 4, 1), dt.date(2022, 6, 30))
)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.semilogy(grezza["data"].to_list(), grezza["chiusura"].to_numpy(),
                linewidth=1.6, linestyle="--")
    ax.axvline(DISCONTINUITA["lunausdt"], linewidth=1.0, linestyle=":")
    ax.set_ylabel("Prezzo di chiusura (USDT, scala log)")
    ax.set_title("La stessa serie letta grezza: da qui in poi è un altro token")
    fig.autofmt_xdate()
    plt.show()

righe = luna.filter(pl.col("data").is_between(dt.date(2022, 5, 5), dt.date(2022, 5, 13)))
partenza = float(righe["chiusura"][0])
for d, p in zip(righe["data"].to_list(), righe["chiusura"].to_numpy()):
    perdita = 1 - p / partenza
    recupero = recupero_necessario(min(perdita, 0.999999))
    print(f"{d}  {p:12.5f} USDT   perdita {perdita:7.3%}   servirebbe +{recupero:,.0%}")

# %% [markdown]
# Guarda la penultima riga: la perdita era già del 98,7%. Il giorno dopo il
# prezzo si è diviso ancora per tremila. **Anche dopo aver perso il 98%, c'era
# ancora tutto da perdere.**
#
# ---
#
# > **EN** — Look at the second-to-last row: the loss was already 98.7%. The
# > next day the price divided again by three thousand. **Even after losing
# > 98%, there was still everything left to lose.**

# %% [markdown]
# ## 2. Quando il prezzo smette di esistere
#
# Il secondo modo di sparire è peggiore, perché non lascia nemmeno un prezzo.
# Nota dove finisce la linea: non arriva a zero, **si interrompe**.
#
# ---
#
# > **EN** — *2. When the price stops existing.* The second way of
# > disappearing is worse, because it doesn't even leave a price. Note where
# > the line ends: it doesn't reach zero, **it breaks off**.

# %%
ftt = carica("fttusdt").sort("data").filter(pl.col("data") >= dt.date(2022, 10, 1))

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.plot(ftt["data"].to_list(), ftt["chiusura"].to_numpy(), linewidth=1.6, marker="o",
            markersize=2.5)
    ax.set_ylabel("Prezzo di chiusura (USDT)")
    fig.autofmt_xdate()
    plt.show()

print(f"ultimo giorno con un prezzo: {ftt['data'][-1]}  ({float(ftt['chiusura'][-1]):.2f} USDT)")
print("dopo quella data non esiste piu' un mercato: non c'e' un prezzo, non c'e' "
      "una quotazione, non c'e' modo di vendere.")

# %% [markdown]
# ## 3. Il paniere, con e senza i morti
#
# Un paniere a peso uguale costruito il 1° aprile 2021. Lo misuriamo in due modi:
# guardando solo ciò che oggi esiste ancora, e guardando **tutto quello che si era
# comprato davvero**.
#
# ---
#
# > **EN** — *3. The basket, with and without the dead.* An equal-weight
# > basket built on April 1, 2021. We measure it two ways: looking only at
# > what still exists today, and looking at **everything that was actually
# > bought**.

# %%
INIZIO = dt.date(2021, 4, 1)  # ← PROVA / TRY: sposta a gennaio 2022 (vedi esercizio 2)
FINE = dt.date(2022, 12, 31)  # ← PROVA / TRY: porta a oggi e guarda cosa cambia
VIVI = ["btcusdt", "ethusdt", "solusdt"]  # ← PROVA / TRY: togli "solusdt" (esercizio 1)
MORTI = ["lunausdt", "fttusdt"]
# NON TOCCARE / DO NOT CHANGE: MORTI deve restare com'è — sono gli unici due
# token defunti congelati nel registro dati; la dimostrazione è proprio che
# le fonti comode non li avrebbero mai lasciati scegliere (vedi esercizio 3)
# MORTI must stay as it is — these are the only two dead tokens frozen in the
# data registry; the whole demonstration is that convenient sources would
# never have let you choose them (see exercise 3)


def curva_paniere(nomi: list[str]) -> tuple[list, np.ndarray]:
    """Paniere a peso uguale, ribilanciato una sola volta all'inizio.

    Due scelte, e vanno dette perché sono le stesse della figura stampata nel
    libro — altrimenti questo quaderno risponderebbe a una domanda diversa da
    quella del capitolo, che è esattamente ciò che non deve succedere.

    **Un asset delistato non sparisce: resta all'ultimo valore noto.** È quanto
    vale davvero per chi ce l'ha in portafoglio, e non è zero: FTT il 15 novembre
    2022 valeva ancora 1,43 dollari, semplicemente non si poteva più vendere.

    **Le serie si leggono con `carica_strumento`**, che si ferma dove
    l'identificativo cambia strumento. Con la serie grezza LUNA risaliva al 6,8%
    del valore iniziale e il paniere dei morti chiudeva a 30,3 invece che a 29,0:
    questo quaderno avrebbe sottostimato del 7% proprio l'errore che esiste per
    misurare.
    """
    calendario = [
        d for d in carica("btcusdt").sort("data")["data"].to_list()
        if INIZIO <= d <= FINE
    ]
    quote = []
    for n in nomi:
        s = carica_strumento(n).sort("data").filter(
            pl.col("data").is_between(INIZIO, FINE)
        )
        mappa = dict(zip(s["data"].to_list(), s["chiusura"].to_numpy()))
        base = mappa[min(mappa)]
        ultimo, riempita = base, []
        for d in calendario:
            ultimo = mappa.get(d, ultimo)
            riempita.append(ultimo / base)
        quote.append(riempita)
    return calendario, np.mean(np.array(quote), axis=0)


date_v, solo_vivi = curva_paniere(VIVI)
date_t, tutti = curva_paniere(VIVI + MORTI)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.plot(date_v, solo_vivi * 100, linewidth=1.8, label="solo i sopravvissuti")
    ax.plot(date_t, tutti * 100, linewidth=1.8, linestyle="--",
            label="tutti, morti compresi")
    ax.axhline(100, linestyle=":", linewidth=0.9)
    ax.set_ylabel("Capitale (base 100)")
    ax.legend()
    fig.autofmt_xdate()
    plt.show()

print(f"paniere dei soli sopravvissuti: {solo_vivi[-1] * 100:.1f}")
print(f"paniere reale, morti compresi:  {tutti[-1] * 100:.1f}")
print(f"differenza:                     {tutti[-1] / solo_vivi[-1] - 1:+.1%}")

# %% [markdown]
# Nessuno dei due numeri è sbagliato: **sono risposte a due domande diverse.**
# La prima è «come sono andati questi tre asset». La seconda è «come sarebbe
# andata a me». Quasi tutti fanno la prima e credono di aver risposto alla
# seconda.
#
# ### Esercizi
#
# 1. Togli `"solusdt"` da `VIVI` e riesegui: la distanza fra le due curve cambia
#    parecchio. Quanto la conclusione dipende da **quali** nomi hai incluso?
# 2. Sposta `INIZIO` a gennaio 2022. Il paniere reale peggiora molto di più di
#    quello dei sopravvissuti: la distorsione cresce quando il periodo contiene
#    più morti.
# 3. L'esercizio che vale il capitolo: prova a ricostruire questa stessa figura
#    usando una fonte gratuita qualunque di dati storici. Scoprirai che i due
#    asset morti **non ci sono**, e otterrai la curva tranquillizzante senza
#    nemmeno accorgerti di aver fatto un errore.
#
# ---
#
# > **EN** — Neither number is wrong: **they are answers to two different
# > questions.** The first is "how did these three assets do". The second is
# > "how would it have gone for me". Almost everyone asks the first and
# > believes they've answered the second.
# >
# > *Exercises.*
# > 1. Remove `"solusdt"` from `VIVI` and rerun: the distance between the two
# >    curves changes quite a bit. How much does the conclusion depend on
# >    **which** names you included?
# > 2. Move `INIZIO` to January 2022. The real basket does much worse than
# >    the survivors-only one: the distortion grows when the period contains
# >    more deaths.
# > 3. The exercise worth the whole chapter: try rebuilding this same figure
# >    using any free source of historical data. You'll find the two dead
# >    assets **aren't there**, and you'll get the reassuring curve without
# >    even noticing you made a mistake.
