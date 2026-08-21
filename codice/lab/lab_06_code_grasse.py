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
# # Lab 6 — La media che mente
#
# *Quaderno del capitolo «La media che mente» di **La matematica di chi perde**.*
#
# Tre cose, sui dati veri: quanto la campana sbaglia sulle code, quanto pochi
# giorni decidono il risultato, e perché i due slogan opposti che si ricavano da
# quella figura sono la stessa affermazione — e nessuno dei due è un consiglio.
#
# ---
#
# > **EN** — *Lab 6 — The lying average.* Notebook for the chapter "The
# > lying average". Three things, on real data: how wrong the bell curve is
# > on the tails, how few days decide the result, and why the two opposite
# > slogans drawn from that figure are the same statement — and neither is
# > advice.

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

from cvbook.dati import carica
from cvbook.metriche import rendimenti

SERIE = "btcusdt"  # ← prova anche "ethusdt" e "solusdt"

df = carica(SERIE).sort("data")
prezzi = df["chiusura"].to_numpy()
date = df["data"].to_list()
r = rendimenti(prezzi)
mu, sigma = float(np.mean(r)), float(np.std(r, ddof=1))

# %% [markdown]
# ## 1. Quanti giorni estremi prevede la campana, e quanti ce ne sono
#
# Se i rendimenti seguissero la curva a campana, il numero di giorni oltre una
# certa distanza dalla media sarebbe calcolabile. Confrontiamolo con quelli che
# ci sono davvero.
#
# ---
#
# > **EN** — *1. How many extreme days the bell curve predicts, and how many
# > there really are.* If returns followed the bell curve, the number of days
# > beyond a certain distance from the mean would be computable. Let's
# > compare it with the real count.

# %%
from math import erfc, sqrt

n = len(r)
print(f"{SERIE}: {n} giorni  ·  media {mu:.4%}  ·  deviazione standard {sigma:.3%}\n")
print(f"{'oltre':>8s} {'previsti dalla campana':>24s} {'osservati':>12s} {'rapporto':>10s}")
for k in (2, 3, 4, 5, 6):
    previsti = n * erfc(k / sqrt(2))
    osservati = int(np.sum(np.abs(r - mu) > k * sigma))
    rapporto = osservati / previsti if previsti > 0 else float("inf")
    print(f"{k:>6d}σ {previsti:24.3f} {osservati:12d} {rapporto:10.1f}x")

peggiore = float(np.min(r))
distanza = abs(peggiore - mu) / sigma
print(f"\ngiorno peggiore: {peggiore:.1%}  →  {distanza:.1f} deviazioni standard dalla media")
print("Secondo il modello a campana un evento del genere non dovrebbe accadere "
      "nemmeno una volta nella storia dell'universo. E' successo, in nove anni.")

curtosi = float(np.mean(((r - mu) / sigma) ** 4))
print(f"\ncurtosi: {curtosi:.1f}   (per la curva a campana vale 3)")

# %% [markdown]
# ## 2. La forma, disegnata
#
# La scala verticale è logaritmica: senza, la differenza sulle code — cioè
# l'unica parte che conta — sarebbe invisibile.
#
# ---
#
# > **EN** — *2. The shape, drawn.* The vertical scale is logarithmic:
# > without it, the difference on the tails — the only part that matters —
# > would be invisible.

# %%
from math import exp, pi

griglia = np.linspace(r.min(), r.max(), 400)
campana = n * np.exp(-((griglia - mu) ** 2) / (2 * sigma**2)) / (sigma * np.sqrt(2 * pi))
larghezza = griglia[1] - griglia[0]

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.hist(r, bins=200, label="quello che e' successo")
    ax.plot(griglia, campana * larghezza, linewidth=2, label="quello che prevede la campana")
    ax.set_yscale("log")
    ax.set_xlabel("Variazione giornaliera")
    ax.set_ylabel("Numero di giorni (scala log)")
    ax.legend()
    plt.show()

# %% [markdown]
# ## 3. Venti giorni su 3.200
#
# Togliamo dalla serie i giorni migliori, poi i peggiori, e guardiamo cosa resta.
#
# ---
#
# > **EN** — *3. Twenty days out of 3,200.* We remove the best days from the
# > series, then the worst, and look at what's left.

# %%
ordine = np.argsort(r)


def senza(indici_da_togliere: np.ndarray) -> float:
    maschera = np.ones(len(r), dtype=bool)
    maschera[indici_da_togliere] = False
    return float(np.prod(1 + r[maschera]))


base = float(np.prod(1 + r))
print(f"tutti i {len(r)} giorni:            {base:9.2f}x\n")
print(f"{'quanti giorni tolti':>22s} {'togliendo i peggiori':>22s} {'togliendo i migliori':>22s}")
for quanti in (1, 5, 10, 20, 50):
    peggiori = senza(ordine[:quanti])
    migliori = senza(ordine[-quanti:])
    print(f"{quanti:>22d} {peggiori:21.2f}x {migliori:21.2f}x")

# %% [markdown]
# ## 4. Ma stanno vicini
#
# Il pezzo che quasi tutti i libri divulgativi omettono: i giorni migliori e i
# peggiori **arrivano nella stessa settimana**. Chi esce per evitare i primi
# manca quasi sempre anche i secondi.
#
# ---
#
# > **EN** — *4. But they sit close together.* The piece almost every
# > popular book leaves out: the best and worst days **arrive in the same
# > week**. Whoever exits to avoid the latter almost always misses the
# > former too.

# %%
peggiori_10 = np.sort(ordine[:10])
migliori_10 = np.sort(ordine[-10:])

print("i dieci giorni peggiori e i dieci migliori, in ordine di calendario:\n")
righe = sorted(
    [(date[i + 1], r[i], "PEGGIORE") for i in peggiori_10]
    + [(date[i + 1], r[i], "migliore") for i in migliori_10]
)
for giorno, variazione, tipo in righe:
    print(f"  {giorno}  {variazione:+7.1%}  {tipo}")

distanze = [
    min(abs(int(m) - int(p)) for p in peggiori_10) for m in migliori_10
]
print(f"\ndistanza mediana fra un giorno migliore e il peggiore piu' vicino: "
      f"{int(np.median(distanze))} giorni")

# %% [markdown]
# ### Esercizi
#
# 1. Cambia `SERIE` in `"ethusdt"` o `"solusdt"`. La curtosi resta molto sopra 3
#    e la concentrazione del risultato in pochi giorni resta: **non è una
#    peculiarità di un asset, è una proprietà dei mercati.**
# 2. Nella terza cella prova a togliere 100 giorni. Quel che resta non assomiglia
#    più a niente di reale: è il motivo per cui «evitare i giorni peggiori» non è
#    un consiglio ma una descrizione di un mondo che non esiste.
# 3. Guarda l'ultima tabella. Prova a immaginare una regola che esca prima di
#    ogni giorno peggiore e rientri prima di ogni giorno migliore: la distanza
#    mediana appena stampata ti dice quanto tempo avresti per accorgertene.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Change `SERIE` to `"ethusdt"` or `"solusdt"`. Kurtosis stays well
# >    above 3 and the concentration of the result in few days remains: **it
# >    is not a quirk of one asset, it's a property of markets.**
# > 2. In the third cell try removing 100 days. What's left no longer
# >    resembles anything real: that's why "avoid the worst days" isn't
# >    advice but a description of a world that doesn't exist.
# > 3. Look at the last table. Try imagining a rule that exits before every
# >    worst day and re-enters before every best day: the median distance
# >    just printed tells you how much time you'd have to notice.
