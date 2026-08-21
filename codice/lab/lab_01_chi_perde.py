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
# # Lab 1 — Chi perde davvero, e quanto
#
# *Quaderno del capitolo «Chi perde davvero, e quanto» di **La matematica di chi perde**.*
#
# Il capitolo mostra tre coordinate senza le quali un risultato non significa
# niente: **su cosa**, **su quale periodo**, **con quali costi**. Qui le vedi
# muoversi.
#
# La figura del libro dice che, su questo asset e in questo periodo, il momento
# in cui si è cominciato conta più di qualunque altra cosa. Il quaderno serve a
# rifare quel conto e — soprattutto — a **smontarlo**, esattamente come fa il
# capitolo: il campione è un solo mercato in un periodo fortunato, e questo va
# guardato in faccia invece che nascosto.
#
# Esegui le celle dall'alto verso il basso. La prima richiede una ventina di
# secondi, le altre sono immediate.
#
# ---
#
# > **EN** — *Lab 1 — Who really loses, and how much.* Notebook for the
# > chapter "Who really loses, and how much". The chapter shows three
# > coordinates without which a result means nothing: **on what**, **over
# > which period**, **at what cost**. Here you watch them move. The book's
# > figure says that, on this asset and in this period, the moment you
# > started matters more than anything else. The notebook redoes that
# > calculation and — above all — **takes it apart**, exactly as the chapter
# > does: the sample is a single market in a lucky period, and that has to be
# > looked at directly, not hidden. Run the cells top to bottom. The first
# > takes about twenty seconds, the rest are immediate.

# %%
# Setup — esegui questa cella per prima.
# %pip install -q "polars>=1.0"
try:
    import avvio  # gia' presente: quaderno rieseguito, o aperto dalla repository
except ModuleNotFoundError:
    import urllib.request

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/cryptoverso-lab/matematica-di-chi-perde/main/codice/lab/avvio.py",
        "avvio.py",
    )
    import avvio

avvio.prepara(["btcusdt"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook.dati import carica, citazione
from cvbook.metriche import drawdown_massimo

df = carica("btcusdt").sort("data")
prezzi = df["chiusura"].to_numpy()
date = df["data"].to_list()
fonte, estratto = citazione("btcusdt")

print(f"serie: {fonte}, estratta il {estratto}")
print(f"periodo: {date[0]} → {date[-1]}  ({len(prezzi)} giorni)")

# %% [markdown]
# ## 1. Quanti ingressi finiscono in perdita, per orizzonte
#
# Per ogni giorno della storia ci chiediamo: chi fosse entrato **quel giorno** e
# uscito dopo N giorni, come sarebbe andata? Poi contiamo la quota di ingressi
# chiusi in perdita.
#
# È il conto che quasi nessuno fa, perché richiede di guardare *tutti* i giorni
# d'ingresso e non solo quello comodo.
#
# ---
#
# > **EN** — *1. How many entries end at a loss, by horizon.* For every day
# > in the history we ask: if someone had entered **that day** and exited
# > after N days, how would it have gone? Then we count the share of entries
# > that closed at a loss. It's the calculation almost nobody makes, because
# > it requires looking at *every* entry day, not just the convenient one.

# %%
ORIZZONTI = [(30, "1 mese"), (90, "3 mesi"), (365, "1 anno"), (730, "2 anni"), (1460, "4 anni")]


def quota_in_perdita(p: np.ndarray, giorni: int) -> float:
    """Frazione di giorni d'ingresso che, dopo `giorni`, si trova sotto zero."""
    if giorni >= len(p):
        return float("nan")
    esiti = p[giorni:] / p[:-giorni] - 1.0
    return float((esiti < 0).mean())


for giorni, etichetta in ORIZZONTI:
    q = quota_in_perdita(prezzi, giorni)
    print(f"{etichetta:>8s}: {q:6.1%} degli ingressi in perdita  ({len(prezzi) - giorni} ingressi)")

# %% [markdown]
# ## 2. Il primo limite: le osservazioni si sovrappongono
#
# I numeri appena stampati sembrano basati su migliaia di casi. Non lo sono.
#
# 2.875 ingressi a dodici mesi su nove anni di storia **non sono 2.875
# esperimenti indipendenti**: sono nove anni guardati da 2.875 angolazioni
# che si accavallano quasi tutte fra loro.
#
# Il conto onesto delle occasioni indipendenti è più vicino a questo.
#
# ---
#
# > **EN** — *2. The first limit: observations overlap.* The numbers just
# > printed look like they're based on thousands of cases. They're not.
# > 2,875 twelve-month entries over nine years of history **are not 2,875
# > independent experiments**: they're nine years seen from 2,875 angles that
# > almost all overlap with each other. The honest count of independent
# > occasions is closer to this.

# %%
for giorni, etichetta in ORIZZONTI:
    sovrapposti = len(prezzi) - giorni
    indipendenti = len(prezzi) // giorni
    print(
        f"{etichetta:>8s}: {sovrapposti:5d} righe nel file, "
        f"ma circa {indipendenti:3d} periodi davvero distinti"
    )

# %% [markdown]
# Guarda la colonna di destra. A quattro anni le osservazioni indipendenti sono
# **due**. Un numero su cui non si costruisce nessuna conclusione.
#
# ---
#
# > **EN** — Look at the right-hand column. At four years the independent
# > observations are **two**. Not a number to build any conclusion on.

# %% [markdown]
# ## 3. Il secondo limite: il periodo è fortunato
#
# Cambia la finestra e guarda cosa succede ai numeri. Il capitolo lo dice
# esplicitamente: la colonna dei quattro anni non dimostra che a quattro anni
# non si perde — dimostra che *in questa finestra* non è successo.
#
# ---
#
# > **EN** — *3. The second limit: the period is lucky.* Change the window
# > and watch what happens to the numbers. The chapter says it explicitly:
# > the four-year column doesn't prove that you don't lose at four years — it
# > proves that *in this window* it didn't happen.

# %%
INIZIO, FINE = "2017-08-17", "2026-06-30"  # ← cambia queste due date

import datetime as dt

maschera = [
    dt.date.fromisoformat(INIZIO) <= d <= dt.date.fromisoformat(FINE) for d in date
]
sotto = prezzi[np.array(maschera)]

print(f"finestra scelta: {INIZIO} → {FINE}  ({len(sotto)} giorni)")
print(f"risultato del compra-e-tieni: {sotto[-1] / sotto[0]:.2f}x")
print(f"calo massimo attraversato:    {drawdown_massimo(sotto):.1%}\n")
for giorni, etichetta in ORIZZONTI:
    q = quota_in_perdita(sotto, giorni)
    print(f"{etichetta:>8s}: {q:6.1%} in perdita")

# %% [markdown]
# ### Esercizi
#
# 1. **Metti `FINE = "2022-12-31"`** ed esegui di nuovo la cella. La colonna dei
#    quattro anni smette di essere zero. Non è cambiato nessun dato: è cambiata
#    la finestra.
# 2. **Metti `INIZIO = "2021-01-01"`.** Il compra-e-tieni scende parecchio. È il
#    capitolo che dice che tre mesi di differenza sull'ingresso valevano
#    129 punti percentuali.
# 3. Cambia `"btcusdt"` in `"ethusdt"` o `"solusdt"` nella cella del setup e in
#    quella del caricamento. La conclusione regge? Su quali orizzonti?
#
# ### Cosa portarsi via
#
# Un risultato non è un numero: è un numero **con** il suo periodo, il suo
# campione e la sua dimensione effettiva. Se una di queste tre cose manca, la
# risposta corretta a «quindi funziona?» è: *non lo so, e non lo sai nemmeno tu.*
#
# ---
#
# > **EN** — *Exercises.*
# > 1. **Set `FINE = "2022-12-31"`** and rerun the cell. The four-year column
# >    stops being zero. No data changed: the window did.
# > 2. **Set `INIZIO = "2021-01-01"`.** Buy-and-hold drops a lot. It's the
# >    chapter that says three months of difference on entry were worth 129
# >    percentage points.
# > 3. Change `"btcusdt"` to `"ethusdt"` or `"solusdt"` in the setup cell and
# >    in the loading one. Does the conclusion hold? On which horizons?
# >
# > *Takeaway.* A result is not a number: it's a number **with** its period,
# > its sample, and its effective size. If any of these three is missing, the
# > correct answer to "so does it work?" is: *I don't know, and neither do
# > you.*
