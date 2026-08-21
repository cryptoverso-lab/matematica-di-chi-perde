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
# *Quaderno del capitolo «Il cimitero dei token» di **Non Fidarti di Me**.*
#
# Questo quaderno contiene i prezzi veri dei due asset morti di cui parla il
# capitolo — uno andato a zero in nove giorni, uno il cui mercato è stato chiuso.
# Conservare quei dati è più difficile di quanto sembri: la maggior parte delle
# fonti comode espone **solo ciò che è ancora attivo**.
#
# Il valore del quaderno non è la cronologia del crollo. È l'ultimo esercizio:
# ricostruire lo stesso paniere guardando solo i sopravvissuti, e vedere che
# risposta tranquillizzante si ottiene.

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

avvio.prepara(["btcusdt", "ethusdt", "solusdt", "lunausdt", "fttusdt"])

# %%
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from cvbook.dati import carica
from cvbook.metriche import recupero_necessario

# %% [markdown]
# ## 1. Nove giorni
#
# Scala logaritmica: ogni tacca vale un fattore dieci. Su scala lineare questo
# grafico sarebbe una riga verticale seguita da una riga piatta — ed è esattamente
# così che i crolli appaiono a chi li guarda mentre accadono.

# %%
luna = carica("lunausdt").sort("data").filter(
    (pl.col("data") >= dt.date(2022, 4, 1)) & (pl.col("data") <= dt.date(2022, 6, 30))
)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.semilogy(luna["data"].to_list(), luna["chiusura"].to_numpy(), linewidth=1.6)
    ax.set_ylabel("Prezzo di chiusura (USDT, scala log)")
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

# %% [markdown]
# ## 2. Quando il prezzo smette di esistere
#
# Il secondo modo di sparire è peggiore, perché non lascia nemmeno un prezzo.
# Nota dove finisce la linea: non arriva a zero, **si interrompe**.

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

# %%
INIZIO = dt.date(2021, 4, 1)
VIVI = ["btcusdt", "ethusdt", "solusdt"]
MORTI = ["lunausdt", "fttusdt"]


def curva_paniere(nomi: list[str]) -> tuple[list, np.ndarray]:
    """Paniere a peso uguale, ribilanciato una sola volta all'inizio.

    Un asset che smette di essere quotato vale zero da quel giorno in poi: è
    l'ipotesi onesta, ed è quella che nessuna fonte comoda ti impone di fare.
    """
    serie = {n: carica(n).sort("data").filter(pl.col("data") >= INIZIO) for n in nomi}
    calendario = sorted(set().union(*[set(s["data"].to_list()) for s in serie.values()]))
    quote = []
    for n, s in serie.items():
        mappa = dict(zip(s["data"].to_list(), s["chiusura"].to_numpy()))
        base = mappa[min(mappa)]
        quote.append([mappa.get(d, 0.0) / base for d in calendario])
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
