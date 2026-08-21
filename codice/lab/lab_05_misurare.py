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
# # Lab 5 — Guardare non è misurare
#
# *Quaderno del capitolo «Cosa vuol dire misurare» di **La matematica di chi perde**.*
#
# Tre sguardi sugli stessi identici dati: il prezzo, le variazioni, la
# distribuzione. Non sono tre livelli di dettaglio — sono **tre domande diverse**,
# e il primo passo del misurare è sapere quale stai facendo.
#
# Poi c'è l'esercizio che conviene fare prima di continuare a leggere il libro:
# distinguere una serie vera da una generata a caso. Le persone ci riescono poco
# più della metà delle volte, cioè poco meglio del lancio di una moneta.
#
# ---
#
# > **EN** — *Lab 5 — Looking is not measuring.* Notebook for the chapter
# > "What measuring means". Three views of the same identical data: price,
# > changes, distribution. They aren't three levels of detail — they are
# > **three different questions**, and the first step of measuring is knowing
# > which one you're asking. Then there's the exercise worth doing before
# > reading further in the book: telling a real series apart from a randomly
# > generated one. People manage it a bit more than half the time — barely
# > better than a coin toss.

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

avvio.prepara(["btcusdt", "ethusdt", "solusdt"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.metriche import rendimenti, volatilita

# %% [markdown]
# ## 1. Tre sguardi
#
# Cambia `SERIE` e riesegui: la forma del primo pannello cambia molto, quella del
# terzo molto meno. È il motivo per cui il terzo permette confronti che il primo
# non permette.
#
# ---
#
# > **EN** — *1. Three views.* Change `SERIE` and rerun: the shape of the
# > first panel changes a lot, the third much less. That's why the third
# > allows comparisons the first doesn't.

# %%
SERIE = "btcusdt"  # ← PROVA / TRY: "ethusdt" · "solusdt" (le tre preparate nel setup)
                   # per un'altra delle 11 serie in codice/dati/registro.json
                   # aggiungila anche a avvio.prepara([...]) qui sopra

df = carica(SERIE).sort("data")
prezzi = df["chiusura"].to_numpy()
date = df["data"].to_list()
r = rendimenti(prezzi)

with avvio.figura("schermo"):
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(13, 4))

    a.semilogy(date, prezzi, linewidth=1.2)
    a.set_title("1. Il prezzo\n«dove siamo arrivati»", fontsize=10)
    a.set_ylabel("Prezzo (scala log)")

    b.plot(date[1:], r * 100, linewidth=0.5)
    b.set_title("2. Le variazioni\n«quanto si muove ogni giorno»", fontsize=10)
    b.set_ylabel("Variazione giornaliera (%)")

    c.hist(r * 100, bins=120)
    c.set_title("3. La distribuzione\n«quanto spesso succede cosa»", fontsize=10)
    c.set_xlabel("Variazione giornaliera (%)")
    c.set_yscale("log")

    for ax in (a, b):
        ax.tick_params(axis="x", rotation=30)
    plt.show()

print(f"{SERIE}: {len(prezzi)} giorni, dal {date[0]} al {date[-1]}")
print(f"volatilita' annualizzata dell'intero periodo: {volatilita(r):.1%}")

# %% [markdown]
# Nel secondo pannello guarda una cosa che nel primo non si vede: **le scosse
# grandi arrivano raggruppate**. Ci sono periodi tranquilli e periodi agitati,
# e i giorni agitati stanno vicini fra loro. È il capitolo sui regimi.
#
# ---
#
# > **EN** — In the second panel look at something the first one doesn't
# > show: **big shocks come clustered**. There are calm periods and turbulent
# > ones, and turbulent days sit close to each other. It's the chapter on
# > regimes.

# %% [markdown]
# ## 2. Vera o finta?
#
# Sei grafici. Alcuni sono prezzi reali, altri sono passeggiate casuali con la
# stessa volatilità. Scrivi la tua risposta **prima** di eseguire la cella dopo.
#
# ---
#
# > **EN** — *2. Real or fake?* Six charts. Some are real prices, others are
# > random walks with the same volatility. Write down your answer **before**
# > running the next cell.

# %%
rng = np.random.default_rng(seed_for("lab-vero-o-finto"))
# NON TOCCARE / DO NOT CHANGE: scrivi la tua risposta PRIMA di eseguire la
# cella con la soluzione. Cambiare il seme per "azzeccarci di più" vanifica
# l'esercizio invece di misurarlo.
FINESTRA = 400  # PROVA / TRY: 400 · 1200 (vedi esercizio 2)

sigma = float(np.std(r, ddof=1))
partenze = rng.integers(0, len(prezzi) - FINESTRA, size=6)
etichette = rng.permutation(["vera", "finta", "vera", "finta", "finta", "vera"])

serie_mostrate = []
for k in range(6):
    if etichette[k] == "vera":
        s = prezzi[partenze[k]: partenze[k] + FINESTRA]
        s = s / s[0] * 100
    else:
        s = 100 * np.cumprod(1 + rng.normal(0.0, sigma, FINESTRA))
    serie_mostrate.append(s)

with avvio.figura("schermo"):
    fig, assi = plt.subplots(2, 3, figsize=(12, 5))
    for k, ax in enumerate(assi.flat):
        ax.plot(serie_mostrate[k], linewidth=1.2)
        ax.set_title(f"grafico {k + 1}", fontsize=10)
        ax.set_xticks([])
    plt.show()

# %%
print("soluzione:")
for k, e in enumerate(etichette):
    print(f"  grafico {k + 1}: {e}")
print(
    "\nQuasi nessuno supera il caso in questo esercizio. Non e' un limite "
    "personale: e' che la percezione trova regolarita' anche nel rumore, ed e' "
    "il motivo per cui serve una misura che possa dire di no."
)

# %% [markdown]
# ## 3. Le quattro domande, in codice
#
# Prima di credere a qualunque numero servono quattro risposte. Qui le vedi
# cambiare il risultato una alla volta.
#
# ---
#
# > **EN** — *3. The four questions, in code.* Before believing any number
# > you need four answers. Here you watch them change the result one at a
# > time.

# %%
print("Su cosa?")
for nome in ("btcusdt", "ethusdt", "solusdt"):
    p = carica(nome).sort("data")["chiusura"].to_numpy()
    print(f"  {nome}: {p[-1] / p[0]:8.2f}x nel proprio periodo disponibile")

print("\nSu quale periodo? (stesso asset, finestre diverse)")
p = carica("btcusdt").sort("data")["chiusura"].to_numpy()
for taglio, etichetta in [(365, "ultimo anno"), (1095, "ultimi 3 anni"), (len(p), "tutto")]:
    s = p[-taglio:]
    print(f"  {etichetta:>14s}: {s[-1] / s[0]:8.2f}x")

print("\nCon quale rappresentazione? (stessi dati, due misure di 'rendimento medio')")
r_btc = rendimenti(p)
media = float(np.mean(r_btc))
composto = float(p[-1] / p[0]) ** (1 / len(r_btc)) - 1
print(f"  media aritmetica giornaliera: {media:.4%}  → su un anno {((1 + media) ** 365 - 1):.1%}")
print(f"  composto giornaliero:         {composto:.4%}  → su un anno {((1 + composto) ** 365 - 1):.1%}")

print("\nConfrontato con cosa? (la domanda che quasi nessuno pone)")
casuali = np.array([
    np.prod(1 + rng.permutation(r_btc)[: len(r_btc) // 2]) for _ in range(200)
])
print(f"  mediana di 200 sotto-campioni casuali della stessa serie: {np.median(casuali):.2f}x")

# %% [markdown]
# ### Esercizi
#
# 1. Nella prima cella cambia serie e guarda **quale pannello cambia di più**.
#    Il terzo è quello che rende confrontabili asset ed epoche diverse: è per
#    quello che tutta la Parte II lavora lì.
# 2. Nella seconda cella porta `FINESTRA` a 1200. Con serie più lunghe l'esercizio
#    diventa un po' più facile — ma molto meno di quanto ti aspetti.
# 3. Nella terza cella, guarda la differenza fra i due «rendimenti medi annui».
#    Sono lo stesso dato. Uno descrive un giorno tipico che non esiste, l'altro
#    quello che è successo davvero a chi era dentro.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the first cell change the series and watch **which panel changes
# >    the most**. The third is the one that makes different assets and eras
# >    comparable: that's why all of Part II works there.
# > 2. In the second cell, raise `FINESTRA` to 1200. With longer series the
# >    exercise becomes a bit easier — but much less than you'd expect.
# > 3. In the third cell, look at the difference between the two "average
# >    annual returns". They're the same data. One describes a typical day
# >    that doesn't exist, the other what actually happened to whoever was in
# >    it.
