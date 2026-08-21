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
# # Lab 8 — Quante cose stai davvero comprando
#
# *Quaderno del capitolo «Quante cose stai davvero comprando» di
# **Non Fidarti di Me**.*
#
# L'analisi delle componenti principali risponde a una domanda che nessun'altra
# misura pone: **quante direzioni indipendenti servono per descrivere il
# movimento di un portafoglio.**
#
# L'esercizio che vale il quaderno è il secondo: aggiungere asset uno alla volta
# e guardare il numero **non muoversi**. È controintuitivo finché non lo si vede.

# %%
# Setup — esegui questa cella per prima.
# %pip install -q "polars>=1.0"
try:
    import avvio
except ModuleNotFoundError:
    import urllib.request

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/cryptoverso-lab/non-fidarti-di-me/main/codice/lab/avvio.py",
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
from cvbook.metriche import rendimenti


def allinea(nomi: list[str], da: dt.date = dt.date(2020, 9, 1)) -> np.ndarray:
    """Rendimenti giornalieri delle serie, sui soli giorni presenti in tutte."""
    pezzi = [
        carica(n).filter(pl.col("data") >= da).select(["data", "chiusura"]).rename({"chiusura": n})
        for n in nomi
    ]
    base = pezzi[0]
    for p in pezzi[1:]:
        base = base.join(p, on="data")
    base = base.sort("data")
    return np.column_stack([rendimenti(base[n].to_numpy()) for n in nomi])


# %% [markdown]
# ## 1. Le componenti, sui tre asset del capitolo
#
# Si parte dalla matrice di correlazione e se ne prendono gli autovalori: sono le
# quote di movimento spiegate da ciascuna direzione indipendente. Tre righe di
# codice, e non serve alcuna libreria specialistica.

# %%
NOMI = ["btcusdt", "ethusdt", "solusdt"]

M = allinea(NOMI)
C = np.corrcoef(M.T)
autovalori = np.linalg.eigvalsh(C)[::-1]
quote = autovalori / autovalori.sum()
cumulata = np.cumsum(quote)

with avvio.figura("schermo"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(11, 4))
    x = np.arange(1, len(quote) + 1)
    sx.bar(x, quote * 100)
    for k, q in enumerate(quote):
        sx.annotate(f"{q:.0%}", xy=(k + 1, q * 100), xytext=(0, 4),
                    textcoords="offset points", ha="center")
    sx.set_xticks(x)
    sx.set_xlabel("Componente")
    sx.set_ylabel("Varianza spiegata (%)")

    dx.plot(x, cumulata * 100, marker="o")
    dx.axhline(90, linestyle=":", linewidth=1.2)
    dx.set_xticks(x)
    dx.set_xlabel("Componenti usate")
    dx.set_ylabel("Varianza cumulata (%)")
    plt.show()

for k, (q, c) in enumerate(zip(quote, cumulata), start=1):
    print(f"componente {k}: {q:6.1%}   cumulata {c:6.1%}")
print(f"\ncomponenti necessarie per arrivare al 90%: {int(np.searchsorted(cumulata, 0.90)) + 1}")

# %% [markdown]
# La prima componente — una sola direzione, cioè sostanzialmente «oggi il settore
# sale o scende» — spiega la gran parte di tutto ciò che accade. Le differenze
# fra i tre asset stanno in quel che resta.

# %% [markdown]
# ## 2. Il numero effettivo di scommesse
#
# Un numero solo al posto del grafico: si sommano i quadrati delle quote e si
# prende l'inverso. Se le componenti pesassero tutte uguale darebbe il numero
# degli asset; se una sola pesasse tutto darebbe uno.

# %%
def numero_effettivo(nomi: list[str]) -> tuple[float, float]:
    m = allinea(nomi)
    c = np.corrcoef(m.T)
    v = np.linalg.eigvalsh(c)[::-1]
    q = v / v.sum()
    rho = float(c[np.triu_indices(len(nomi), 1)].mean())
    da_correlazione = 1.0 / (1 / len(nomi) + (1 - 1 / len(nomi)) * rho)
    return float(1.0 / np.sum(q**2)), da_correlazione


da_componenti, da_correlazione = numero_effettivo(NOMI)
print(f"numero effettivo di scommesse (componenti):        {da_componenti:.2f}")
print(f"numero effettivo di scommesse (correlazione media): {da_correlazione:.2f}")
print("\nDue metodi con assunzioni diverse. Il secondo assume che tutte le coppie "
      "abbiano la stessa correlazione; il primo vede la struttura reale. Quando "
      "concordano sull'ordine di grandezza, la conclusione e' molto piu' solida.")

# %% [markdown]
# ## 3. L'esercizio: aggiungi asset e guarda il numero non muoversi

# %%
print(f"{'portafoglio':>34s} {'asset':>6s} {'scommesse effettive':>20s}")
for k in range(1, len(NOMI) + 1):
    sottoinsieme = NOMI[:k]
    if k == 1:
        effettivo = 1.0
    else:
        effettivo, _ = numero_effettivo(sottoinsieme)
    print(f"{' + '.join(sottoinsieme):>34s} {k:6d} {effettivo:20.2f}")

print("\nAggiungere asset dello stesso tipo non aggiunge dimensioni: aggiunge "
      "costi e cose da seguire.")

# %% [markdown]
# ## 4. Stabilità nel tempo
#
# I limiti vanno guardati, non nominati. Le componenti calcolate su un periodo
# tranquillo possono essere diverse da quelle calcolate su un periodo di stress:
# la buona pratica è calcolarle su più finestre e vedere quanto sono stabili.

# %%
FINESTRA = 250
prime = []
for i in range(FINESTRA, len(M), 25):
    blocco = M[i - FINESTRA:i]
    v = np.linalg.eigvalsh(np.corrcoef(blocco.T))[::-1]
    prime.append(v[0] / v.sum())

prime = np.array(prime)
with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(prime * 100, marker="o", markersize=3)
    ax.set_xlabel(f"Finestre mobili di {FINESTRA} giorni")
    ax.set_ylabel("Varianza spiegata dalla prima componente (%)")
    ax.set_ylim(0, 100)
    plt.show()

print(f"prima componente: minimo {prime.min():.1%}, massimo {prime.max():.1%}, "
      f"media {prime.mean():.1%}")

# %% [markdown]
# ### Esercizi
#
# 1. Togli `"solusdt"` da `NOMI` e riesegui: con due soli asset la prima
#    componente spiega ancora di più. Non è un miglioramento della misura, è che
#    con meno serie c'è meno struttura da trovare.
# 2. Nella quarta cella riduci `FINESTRA` a 60. La prima componente diventa molto
#    più instabile: quanto di quella instabilità è del mercato e quanto è
#    dell'aver usato meno dati?
# 3. Applica lo stesso codice ai tuoi **indicatori** invece che agli asset. Se
#    due o tre componenti spiegano quasi tutto, i tuoi otto indicatori stanno
#    misurando la stessa cosa in modi leggermente diversi.
