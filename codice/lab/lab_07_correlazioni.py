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
# # Lab 7 — Quando la diversificazione svanisce
#
# *Quaderno del capitolo «Quando la diversificazione svanisce» di
# **La matematica di chi perde**.*
#
# Tre cose. Prima: il modo intuitivo di misurare la correlazione nei crolli dà
# la risposta **sbagliata**, e qui lo vedi succedere. Seconda: la correlazione
# non sta ferma, e sale proprio quando servirebbe che non salisse. Terza: quanto
# vale davvero avere N asset, con il conto che quasi nessuno fa.
#
# ---
#
# > **EN** — *Lab 7 — When diversification vanishes.* Notebook for the
# > chapter "When diversification vanishes". Three things. First: the
# > intuitive way of measuring correlation during crashes gives the
# > **wrong** answer, and here you watch it happen. Second: correlation
# > doesn't sit still, and it rises exactly when you'd need it not to.
# > Third: what having N assets is really worth, with the calculation almost
# > nobody does.

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
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from cvbook.dati import carica
from cvbook.metriche import drawdown, rendimenti

NOMI = ["btcusdt", "ethusdt", "solusdt"]  # ← PROVA / TRY: aggiungi "ftsemib" o "eni"
                                          # (aggiungili anche a avvio.prepara([...]))
DA = dt.date(2020, 9, 1)  # PROVA / TRY: sposta la data d'inizio

serie = [
    carica(n).filter(pl.col("data") >= DA).select(["data", "chiusura"]).rename({"chiusura": n})
    for n in NOMI
]
tabella = serie[0]
for s in serie[1:]:
    tabella = tabella.join(s, on="data")
tabella = tabella.sort("data")

date = tabella["data"].to_list()[1:]
M = np.column_stack([rendimenti(tabella[n].to_numpy()) for n in NOMI])
print(f"{len(NOMI)} serie allineate, {len(M)} giorni comuni, dal {date[0]} al {date[-1]}")

# %% [markdown]
# ## 1. Il metodo intuitivo, e perché è sbagliato
#
# L'idea naturale: prendo i giorni peggiori e calcolo la correlazione lì. Sembra
# ovvia, ed è un artefatto — selezionando in base a un valore estremo di una
# variabile se ne restringe la variabilità, e la correlazione risulta distorta
# verso il basso.
#
# ---
#
# > **EN** — *1. The intuitive method, and why it's wrong.* The natural
# > idea: take the worst days and compute correlation there. It seems
# > obvious, and it's an artifact — selecting on an extreme value of one
# > variable restricts its variability, and the correlation ends up biased
# > downward.

# %%
coppie = np.triu_indices(len(NOMI), 1)


def correlazione_media(blocco: np.ndarray) -> float:
    return float(np.corrcoef(blocco.T)[coppie].mean())


primo = M[:, 0]
peggiori = np.argsort(primo)[: len(primo) // 20]  # il 5% dei giorni peggiori
                                                   # PROVA / TRY: // 5 per il 20% (vedi esercizio 3)

print(f"correlazione media su tutto il periodo:        {correlazione_media(M):.3f}")
print(f"correlazione media sul 5% dei giorni peggiori: {correlazione_media(M[peggiori]):.3f}")
print("\nSembra che nei crolli la correlazione SCENDA. E' falso, ed e' il "
      "risultato del modo in cui abbiamo selezionato i giorni.")

# %% [markdown]
# ## 2. Il metodo corretto: finestre temporali
#
# Si misura la correlazione su finestre mobili e poi si guarda **in quali periodi
# è più alta**. Nessuna selezione basata sul valore delle variabili.
#
# ---
#
# > **EN** — *2. The correct method: time windows.* Correlation is measured
# > on rolling windows, then you look at **in which periods it's higher**.
# > No selection based on the value of the variables.

# %%
FINESTRA = 60  # PROVA / TRY: 20 · 60 · 200 (vedi esercizio 2)

corr = np.array([correlazione_media(M[i - FINESTRA:i]) for i in range(FINESTRA, len(M))])
date_c = date[FINESTRA:]
dd = drawdown(np.concatenate([[1.0], np.cumprod(1 + primo)]))[FINESTRA + 1:]
brutti = dd < -0.30

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(date_c, 0, 1, where=brutti, step="mid", alpha=0.25,
                    label="mercato oltre il 30% sotto il massimo")
    ax.plot(date_c, corr, linewidth=1.3, label="correlazione media a 60 giorni")
    ax.axhline(corr.mean(), linestyle=":", linewidth=1.2)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Correlazione media")
    ax.legend(loc="lower left")
    fig.autofmt_xdate()
    plt.show()

print(f"minimo {corr.min():.2f}   massimo {corr.max():.2f}   media {corr.mean():.2f}")
print(f"media nei periodi difficili: {corr[brutti].mean():.2f}")
print(f"media nel resto del tempo:   {corr[~brutti].mean():.2f}")

# %% [markdown]
# ## 3. Quanto vale davvero avere N asset
#
# La quota di oscillazione che resta, rispetto a possederne uno solo: uno diviso
# il numero degli asset, più la correlazione moltiplicata per tutto il resto. E
# poi la radice quadrata.
#
# ---
#
# > **EN** — *3. What having N assets is really worth.* The share of swing
# > that remains, compared to holding just one: one divided by the number of
# > assets, plus correlation times the rest. Then the square root.

# %%
def oscillazione_residua(n: int, rho: float) -> float:
    return float(np.sqrt(1 / n + (1 - 1 / n) * rho))


rho_misurata = correlazione_media(M)
print(f"correlazione media misurata su queste serie: {rho_misurata:.2f}\n")
print(f"{'asset':>6s} {'indipendenti':>14s} {'a corr. 0,3':>14s} "
      f"{f'a corr. {rho_misurata:.2f}':>14s} {'a corr. 0,9':>14s}")
for n in (2, 3, 4, 5, 10, 15, 30):
    valori = "".join(f"{oscillazione_residua(n, rho) * 100:13.1f}%"
                     for rho in (0.0, 0.3, rho_misurata, 0.9))
    print(f"{n:6d} {valori}")

n_eff = 1 / (1 / 3 + (1 - 1 / 3) * rho_misurata)
print(f"\nnumero di asset DAVVERO indipendenti equivalenti ai tuoi 3: {n_eff:.2f}")

# %% [markdown]
# ### Esercizi
#
# 1. Nella terza cella guarda la colonna della correlazione misurata: fra 4 e 15
#    asset la riduzione cambia di pochissimo. **Dal quinto in poi paghi costi e
#    complessità senza comprare protezione.**
# 2. Cambia `FINESTRA` da 60 a 20 e poi a 200. Con finestre corte la correlazione
#    balla molto di più: quanto della sua instabilità è del mercato e quanto è
#    della misura?
# 3. Riesegui la prima cella prendendo il 20% dei giorni peggiori invece del 5%.
#    L'artefatto si attenua. È la dimostrazione che era un effetto della
#    selezione e non un fatto del mercato.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the third cell look at the measured-correlation column: between 4
# >    and 15 assets the reduction changes very little. **From the fifth one
# >    on you pay cost and complexity without buying protection.**
# > 2. Change `FINESTRA` from 60 to 20 and then to 200. With short windows
# >    correlation swings much more: how much of its instability is the
# >    market's, and how much is the measurement's?
# > 3. Rerun the first cell taking the worst 20% of days instead of 5%. The
# >    artifact fades. It's proof that it was an effect of the selection, not
# >    a fact about the market.
